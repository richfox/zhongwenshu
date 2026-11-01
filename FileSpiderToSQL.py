# -*- coding: utf-8 -*-
"""Import locally saved Dangdang desktop product pages into ECS."""

import ftplib
import os
import re
import shutil
import sys
import time
from copy import deepcopy
from pathlib import Path
from urllib.parse import quote, unquote, urlsplit
from xml.etree import ElementTree

import pymysql
import pinyin
from lxml import etree, html as lxml_html
from PIL import Image


def generate_sn(title):
    value = pinyin.get_initial(title or '').upper()
    value = re.sub(r'[^A-Z0-9_]+', '', value)
    return (value[:2] if len(value) > 2 else value) + str(int(time.time()))


def load_product_ids(config_file):
    root = ElementTree.parse(config_file).getroot()
    product_ids = []
    for node in root.findall('./http/url/productID'):
        product_id = (node.text or '').strip()
        if product_id and product_id not in product_ids:
            product_ids.append(product_id)
    return product_ids


def read_page(path):
    """Let libxml honor the saved document's GBK/UTF-8 charset declaration."""
    parser = lxml_html.HTMLParser(encoding=None, recover=True)
    return lxml_html.fromstring(Path(path).read_bytes(), parser=parser)


def node_text(node):
    return ' '.join(' '.join(node.itertext()).split()) if node is not None else ''


def first_text(tree, expressions):
    for expression in expressions:
        nodes = tree.xpath(expression)
        for node in nodes:
            value = node_text(node) if hasattr(node, 'itertext') else str(node).strip()
            if value:
                return value
    return ''


def field_from_specs(tree, *labels):
    """Read product attributes from Dangdang's detail_describe list items."""
    for item in tree.xpath('//*[@id="detail_describe"]//li'):
        text = re.sub(r'\s+', '', node_text(item).replace('\xa0', ' '))
        for label in labels:
            match = re.search(re.escape(re.sub(r'\s+', '', label)) + r'[：:]\s*(.*)', text)
            if match:
                return match.group(1).strip()
    return ''


def parse_book(tree, product_id):
    title = first_text(tree, [
        '//*[@id="product_info"]//h1/@title',
        '//*[@id="product_info"]//h1',
        '//meta[@property="og:title"]/@content',
        '//title',
    ])
    title = re.sub(r'\s*[-|｜]\s*当当图书\s*$', '', title).strip()
    author = first_text(tree, ['//*[@id="author"]'])
    author = re.sub(r'^作者\s*[：:]\s*', '', author).strip()
    press = first_text(tree, [
        '//*[@id="product_info"]/div[2]/span[2]/a',
        '//*[@id="product_info"]//*[contains(normalize-space(.), "出版社")]/following-sibling::a[1]',
    ])
    pressdate = first_text(tree, ['//*[@id="product_info"]/div[2]/span[3]'])
    pressdate = re.sub(r'^\s*出版时间\s*[：:]\s*', '', pressdate).strip()

    isbn = field_from_specs(tree, 'ISBN', '国际标准书号ISBN')
    isbn = ''.join(re.findall(r'\d+', isbn))
    size = field_from_specs(tree, '开本')
    if not size:
        size = field_from_specs(tree, '开', '本')
    paper = field_from_specs(tree, '纸张')
    packing = field_from_specs(tree, '包装')
    packing = next((item for item in ('平装', '精装', '盒装') if item in packing), '')

    shopprice = first_text(tree, [
        '//*[@id="dd-price"]', '//*[@id="saleprice"]',
        '//*[contains(@class,"price_d")]//text()',
        '//*[@id="product_info"]//*[contains(@class,"price")]',
    ])
    prices = re.findall(r'\d+(?:\.\d{1,2})?', shopprice.replace(',', ''))
    shopprice = prices[0] if prices else '0.00'
    marketprice = first_text(tree, [
        '//*[@id="original-price"]', '//*[@id="originalPrice"]',
        '//*[@id="product_info"]//*[contains(@class,"price_m")]',
    ])
    prices = re.findall(r'\d+(?:\.\d{1,2})?', marketprice.replace(',', ''))
    marketprice = prices[0] if prices else shopprice

    image_src = first_text(tree, ['//*[@id="modalBigImg"]/@src'])
    description = build_description(tree)
    return {
        'product_id': product_id,
        'title': title,
        'author': author,
        'press': press,
        'isbn': isbn,
        'pressdate': pressdate,
        'size': size,
        'packing': packing,
        'paper': paper,
        'shopprice': shopprice,
        'marketprice': marketprice,
        'image_src': image_src,
        'description': description,
    }


def get_description_nodes(tree):
    """Select the complete detail sections included in the imported description."""
    section_class = 'contains(concat(" ",normalize-space(@class)," ")," section ")'
    descrip_class = 'contains(concat(" ",normalize-space(@class)," ")," descrip ")'
    # Select complete content sections, rather than just their descrip children.
    # The outer #detail container also has class="section" on saved Dangdang pages.
    details = tree.xpath('//*[%s and *[%s]]' % (section_class, descrip_class))
    if not details:
        details = tree.xpath('//*[@id="product_detail"] | //*[@id="description"] | '
                             '//*[%s]' % descrip_class)
    if not details:
        details = tree.xpath('//*[@id="detail_describe"]')

    selected = set(details)
    return [node for node in details
            if not any(parent in selected for parent in node.iterancestors())]


def build_description(tree):
    """Keep the saved sections' original tags, titles, IDs and attributes."""
    sections = []
    for original in get_description_nodes(tree):
        node = deepcopy(original)
        for link in node.xpath('.//a[contains(concat(" ",normalize-space(@class)," "),'
                               '" section_show_more ")]'):
            link.drop_tree()
        for textarea in node.xpath('.//textarea'):
            if re.search(r'(?:^|;)\s*display\s*:\s*none\s*(?:!important\s*)?(?:;|$)',
                         textarea.get('style', ''), re.I):
                textarea.drop_tree()
        sections.append(etree.tostring(node, encoding='unicode', method='html', with_tail=False))
    markup = ''.join(sections)
    if not markup:
        markup = '<p>本商品暂无详情。</p>'
    return '<div><zws-product>%s</zws-product></div>' % markup


def image_urls_blank():
    return dict.fromkeys(('ori', 'goods', 'thumb', 'galleryori', 'gallerygoods', 'gallerythumb'), '')


def find_local_image(page_path, image_src):
    """Resolve saved asset paths, including four-character browser suffixes."""
    page_path = Path(page_path)
    reference = Path(unquote(urlsplit(image_src.replace('\\', '/')).path))
    asset_dir = page_path.with_name(page_path.stem + '_files')
    candidates = [page_path.parent / reference, asset_dir / reference.name]
    for candidate in candidates:
        if candidate.is_file():
            return candidate.resolve()

    def original_stem(path):
        return re.sub(r'_[A-Za-z0-9]{4}$', '', path.stem).casefold()

    matches = set()
    for directory in {candidates[0].parent, asset_dir}:
        if not directory.is_dir():
            continue
        for candidate in directory.iterdir():
            if (candidate.is_file() and candidate.suffix.lower() == reference.suffix.lower()
                    and original_stem(candidate) == original_stem(reference)):
                matches.add(candidate.resolve())
    if len(matches) == 1:
        return matches.pop()
    raise FileNotFoundError('Local image is missing or ambiguous: %s (%s)' %
                            (image_src, page_path))


def upload_description_images(tree, page_path, fconn):
    """Store detail images in uploadpath/web_img and limit their width."""
    pending = []
    images = [image for section in get_description_nodes(tree)
              for image in section.xpath('.//img')]
    for node in images:
        image_src = ((node.get('data-original') or '').strip()
                     or (node.get('src') or '').strip())
        if not image_src:
            continue
        pending.append((node, find_local_image(page_path, image_src)))
    if not pending:
        return

    server = fconn.get('server')
    if server is not None:
        previous_dir = server.pwd()
        try:
            try:
                server.cwd('web_img')
            except ftplib.error_perm:
                server.mkd('web_img')
        finally:
            server.cwd(previous_dir)
    else:
        output_dir = Path(fconn['root']) / fconn['path'] / 'web_img'
        output_dir.mkdir(parents=True, exist_ok=True)
    uploaded = {}
    for node, image_path in pending:
        if image_path not in uploaded:
            if server is not None:
                with image_path.open('rb') as source:
                    server.storbinary('STOR web_img/' + image_path.name, source)
            else:
                shutil.copyfile(str(image_path), str(output_dir / image_path.name))
            uploaded[image_path] = fconn['path'] + 'web_img/' + quote(image_path.name)
        node.set('src', uploaded[image_path])
        node.set('width', '716')
        if 'data-original' in node.attrib:
            node.set('data-original', uploaded[image_path])


def _store_image(image, sn, fconn):
    result = image_urls_blank()
    ext = (image.format or 'JPEG').lower()
    if ext == 'jpeg':
        ext = 'jpg'
    save_format = 'JPEG' if ext == 'jpg' else ext.upper()

    def save(source_image, name, directory):
        if 'server' in fconn:
            import tempfile
            with tempfile.NamedTemporaryFile(suffix='.' + ext, delete=False) as temp:
                temp_path = temp.name
            try:
                source_image.save(temp_path, format=save_format)
                target = directory + '/' + name + '.' + ext
                with open(temp_path, 'rb') as source:
                    fconn['server'].storbinary('STOR ' + target, source)
                return fconn['path'] + target
            finally:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
        root = fconn['root']
        output_dir = os.path.join(root, fconn['path'].replace('/', os.sep), directory)
        os.makedirs(output_dir, exist_ok=True)
        source_image.save(os.path.join(output_dir, name + '.' + ext), format=save_format)
        return fconn['path'] + directory + '/' + name + '.' + ext

    original = image.copy()
    result['ori'] = save(original, sn, 'source_img')
    result['galleryori'] = save(original, sn + '_P', 'source_img')
    result['gallerygoods'] = save(original, sn + '_G_P', 'goods_img')
    thumb = original.copy()
    thumb.thumbnail((230, 230), Image.Resampling.LANCZOS)
    result['goods'] = save(thumb, sn + '_G', 'goods_img')
    tiny = original.copy()
    tiny.thumbnail((100, 100), Image.Resampling.LANCZOS)
    result['thumb'] = save(tiny, sn + '_T', 'thumb_img')
    result['gallerythumb'] = save(tiny, sn + '_T_P', 'thumb_img')
    return result


def save_local_picture(page_path, image_src, sn, fconn):
    image_path = (Path(page_path).parent / image_src.split('?', 1)[0]).resolve()
    if not image_src or not image_path.is_file():
        print('Cover image is missing locally: %s' % image_src)
        return image_urls_blank()
    try:
        with Image.open(str(image_path)) as source:
            source.load()
            # Save each size from the right source dimensions, as in SpiderToSQL.
            original = source.copy()
            ext = source.format or 'JPEG'
            original.format = ext
            return _store_image(original, sn, fconn)
    except Exception as error:
        print('Could not process local cover image %s: %s' % (image_path, error))
        return image_urls_blank()


def table_names(dbname):
    if dbname == 'zhongw_test':
        return ('ecs_test_goods', 'ecs_test_goods_attr', 'ecs_test_goods_cat',
                'ecs_test_goods_gallery')
    if dbname == 'zhongwenshu_db1':
        return ('ecs_goods', 'ecs_goods_attr', 'ecs_goods_cat', 'ecs_goods_gallery')
    raise ValueError('Unsupported database: %s' % dbname)


def insert_product(connection, dbname, book, images, sn):
    goods, goods_attr, goods_cat, goods_gallery = table_names(dbname)
    attrs = {1: book['author'], 2: book['press'], 3: book['isbn'], 4: book['pressdate'],
             5: book['size'], 7: book['packing'], 10: book['paper'],
             232: '¥' + book['marketprice']}
    sql = """INSERT INTO {goods} (`goods_id`, `cat_id`, `goods_sn`, `goods_name`,
        `goods_name_style`, `click_count`, `brand_id`, `provider_name`, `goods_number`,
        `goods_weight`, `market_price`, `virtual_sales`, `shop_price`, `promote_price`,
        `promote_start_date`, `promote_end_date`, `warn_number`, `keywords`, `goods_brief`,
        `goods_desc`, `goods_thumb`, `goods_img`, `original_img`, `is_real`, `extension_code`,
        `is_on_sale`, `is_alone_sale`, `is_shipping`, `integral`, `add_time`, `sort_order`,
        `is_delete`, `is_best`, `is_new`, `is_hot`, `is_promote`, `bonus_type_id`, `last_update`,
        `goods_type`, `seller_note`, `give_integral`, `rank_integral`, `suppliers_id`, `is_check`)
        VALUES (NULL, %s, %s, %s,
        '+', '0', '0', '', %s,
        %s, %s, '', %s, '0.00',
        '0', '0', '1', '', '',
        %s, %s, %s, %s, '1', '',
        '0', '1', '0', '0', %s, '100',
        '0', '0', '1', '0', '0', '0', '0',
        %s, '', '-1', '-1', '0', NULL)""".format(goods=goods)
    with connection.cursor() as cursor:
        # Euro prices are filled in manually after import.
        cursor.execute(sql, (
            134, sn, book['title'],
            '0',
            '0.000', '0.00', '0.00',
            book['description'], images['thumb'], images['goods'], images['ori'],
            str(int(time.time())),
            '1',
        ))

        #唯一商品编号
        cursor.execute('SELECT `goods_id` FROM ' + goods + ' WHERE `goods_sn`=%s', sn)
        row = cursor.fetchone()
        if not row:
            raise RuntimeError('Inserted product could not be found: %s' % sn)
        goods_id = row[0]

        #填入书籍信息
        for attr_id, attr in attrs.items():
            cursor.execute('INSERT INTO ' + goods_attr +
                           ' (`goods_attr_id`, `goods_id`, `attr_id`, `attr_value`, `attr_price`) '
                           "VALUES (NULL, %s, %s, %s, '0')",
                           (goods_id, attr_id, attr))

        #新品到货
        cursor.execute('INSERT INTO ' + goods_cat +
                       " (`goods_id`, `cat_id`) VALUES (%s, '65')", goods_id)

        #填入书籍画册
        if images['galleryori']:
            cursor.execute('INSERT INTO ' + goods_gallery +
                           ' (`img_id`, `goods_id`, `img_url`, `img_desc`, `thumb_url`, `img_original`) '
                           "VALUES (NULL, %s, %s, '', %s, %s)",
                           (goods_id, images['gallerygoods'], images['gallerythumb'], images['galleryori']))
    return goods_id


def load_server_config(config_file):
    root = ElementTree.parse(config_file).getroot()
    active = next((node for node in root if node.get('using') == '1'), None)
    if active is None:
        raise ValueError('No enabled server configuration in %s' % config_file)

    def values(parent, names):
        node = active.find(parent)
        if node is None:
            raise ValueError('Missing %s settings in %s' % (parent, config_file))
        return tuple((node.findtext(name) or '').strip() for name in names)

    mysql = values('mysql', ('host', 'user', 'password', 'db', 'charset'))
    ftp = values('ftp', ('host', 'user', 'password', 'uploadpath', 'tls'))
    return mysql, ftp


def open_image_connection(ftp, dbname):
    fconn = {'path': ftp[3].replace('\\', '/').rstrip('/') + '/'}
    if re.match(r'.*your-server\.de$', ftp[0]):
        cls = ftplib.FTP_TLS if ftp[4] == '1' else ftplib.FTP
        fconn['server'] = cls(ftp[0], ftp[1], ftp[2])
        if ftp[4] == '1':
            fconn['server'].prot_p()
        fconn['server'].cwd(fconn['path'])
    elif 'local' in ftp[0]:
        root = Path('C:/xampp')
        if not root.exists() and Path(str(root) + '.lnk').exists():
            import win32com.client
            root = Path(win32com.client.Dispatch('WScript.Shell').CreateShortCut(
                str(root) + '.lnk').Targetpath)
        root = root / 'htdocs' / 'ecshop'
        fconn['root'] = str(root)
    else:
        raise ValueError('Unsupported image server: %s' % ftp[0])
    return fconn


def run(product_config='dangdangConfig.xml', server_config='myServerConfig.sxml',
        page_dir='bookwebsite'):
    product_ids = load_product_ids(product_config)
    if not product_ids:
        print('No product IDs found in %s' % product_config)
        return False
    mysql, ftp = load_server_config(server_config)
    host, username, password, dbname, charset = mysql
    connection = pymysql.connect(host=host, user=username, password=password,
                                 database=dbname, charset=charset)
    fconn = open_image_connection(ftp, dbname)
    try:
        for product_id in product_ids:
            page_path = Path(page_dir) / (product_id + '.htm')
            if not page_path.is_file():
                print('Saved page not found: %s' % page_path)
                continue
            try:
                tree = read_page(page_path)
                book = parse_book(tree, product_id)
                if not book['title']:
                    print('Could not find product title in %s' % page_path)
                    continue
                upload_description_images(tree, page_path, fconn)
                book['description'] = build_description(tree)
                sn = generate_sn(book['title'])
                images = save_local_picture(page_path, book['image_src'], sn, fconn)
                goods_id = insert_product(connection, dbname, book, images, sn)
                connection.commit()
                print('Imported %s (goods_id=%s)' % (book['title'], goods_id))
            except Exception as error:
                connection.rollback()
                print('Failed to import %s: %s' % (page_path, error))
    finally:
        connection.close()
        if 'server' in fconn:
            fconn['server'].quit()
    return True


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) > 2:
        print('Usage: python .\\dangdang.py -f [dangdangConfig.xml] [myServerConfig.sxml]')
        return False
    product_config = argv[0] if argv else 'dangdangConfig.xml'
    server_config = argv[1] if len(argv) == 2 else 'myServerConfig.sxml'
    return run(product_config, server_config)


if __name__ == '__main__':
    main()
