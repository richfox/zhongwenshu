#-*-coding:utf-8-*-
"""Crawler/importer for product.m.dangdang.com product pages.

The mobile site exposes the complete product record in the JavaScript variable
``prd_info``.  Parsing that record is substantially more stable than scraping
the rendered HTML elements used by the legacy desktop crawler.
"""

import html
import json
import os
import re
import sys
import time
import ftplib
import webbrowser
import xml.etree.ElementTree as ElementTree

import pymysql
import pinyin
import ImageProcess

import utility


def generate_sn(hanzi):
    """Create an ECS-compatible goods number, matching the desktop importer."""
    value = pinyin.get_initial(hanzi).upper()
    value = re.sub('[^A-Z0-9_]+', '', value)[:2]
    return value + str(int(time.time()))


def split_params(url):
    params = {}
    for item in re.split(r'[?&]', url)[1:]:
        key, separator, value = item.partition('=')
        params[key] = value if separator else ''
    return params


def remove_params(url):
    return url.split('?', 1)[0]


def _blank_images():
    return {'ori': '', 'goods': '', 'thumb': '', 'galleryori': '',
            'gallerygoods': '', 'gallerythumb': ''}


def save_first_picture(image_url, sn, fconn):
    """Store one mobile image using the same ECS path conventions as before."""
    result = _blank_images()
    if not image_url:
        return result
    image = ImageProcess.Processor(image_url)
    if not image.Loaded():
        return result
    try:
        if 'server' in fconn:
            source = image.Save('./temp', sn, image.Format())
            target = image.Upload(fconn['server'], source, 'source_img', sn, image.Format())
            if target:
                result['ori'] = fconn['path'] + target
            target = image.Upload(fconn['server'], source, 'source_img', sn + '_P', image.Format())
            if target:
                result['galleryori'] = fconn['path'] + target
            target = image.Upload(fconn['server'], source, 'goods_img', sn + '_G_P', image.Format())
            if target:
                result['gallerygoods'] = fconn['path'] + target
            if image.Width() > 230 and image.Height() > 230:
                image.Thumb(230, 230)
            source = image.Save('./temp', sn + '_G', image.Format())
            target = image.Upload(fconn['server'], source, 'goods_img', sn + '_G', image.Format())
            if target:
                result['goods'] = fconn['path'] + target
            if image.Width() > 100 and image.Height() > 100:
                image.Thumb(100, 100)
            source = image.Save('./temp', sn + '_T', image.Format())
            target = image.Upload(fconn['server'], source, 'thumb_img', sn + '_T', image.Format())
            if target:
                result['thumb'] = fconn['path'] + target
            target = image.Upload(fconn['server'], source, 'thumb_img', sn + '_T_P', image.Format())
            if target:
                result['gallerythumb'] = fconn['path'] + target
        elif 'local' in fconn:
            root = 'C:/xampp'
            if not os.path.exists(root) and os.path.exists(root + '.lnk'):
                import win32com.client
                root = win32com.client.Dispatch('WScript.Shell').CreateShortCut(root + '.lnk').Targetpath
            root += '/htdocs/ecshop/test/' if re.match(r'.*test.*', fconn['local']) else '/htdocs/ecshop/'
            image.Save(root + fconn['path'] + 'source_img/', sn, image.Format())
            image.Save(root + fconn['path'] + 'source_img/', sn + '_P', image.Format())
            image.Save(root + fconn['path'] + 'goods_img/', sn + '_G_P', image.Format())
            result['ori'] = fconn['path'] + 'source_img/' + sn + '.' + image.Format()
            result['galleryori'] = fconn['path'] + 'source_img/' + sn + '_P.' + image.Format()
            result['gallerygoods'] = fconn['path'] + 'goods_img/' + sn + '_G_P.' + image.Format()
            if image.Width() > 230 and image.Height() > 230:
                image.Thumb(230, 230)
            image.Save(root + fconn['path'] + 'goods_img/', sn + '_G', image.Format())
            result['goods'] = fconn['path'] + 'goods_img/' + sn + '_G.' + image.Format()
            if image.Width() > 100 and image.Height() > 100:
                image.Thumb(100, 100)
            image.Save(root + fconn['path'] + 'thumb_img/', sn + '_T', image.Format())
            image.Save(root + fconn['path'] + 'thumb_img/', sn + '_T_P', image.Format())
            result['thumb'] = fconn['path'] + 'thumb_img/' + sn + '_T.' + image.Format()
            result['gallerythumb'] = fconn['path'] + 'thumb_img/' + sn + '_T_P.' + image.Format()
    except Exception:
        print('image import failed: %s' % sys.exc_info()[0])
        return _blank_images()
    return result


def _load_prd_info(page):
    """Read the JSON assigned to ``var prd_info`` without using brittle regex."""
    match = re.search(r'\bvar\s+prd_info\s*=\s*', page or '')
    if not match:
        return {}
    try:
        value, _ = json.JSONDecoder().raw_decode(page[match.end():].lstrip())
    except (TypeError, ValueError):
        return {}
    return value if isinstance(value, dict) else {}


_SECTION_IDS = {
    '产品特色': 'feature',
    '推荐语': 'feature',
    '内容简介': 'abstract',
    '简介': 'abstract',
    '目录': 'catalog',
    '作者简介': 'authorIntroduction',
    '书摘插画': 'attachImage',
    '其他': 'attachImage',
    '出版信息': 'publishInfo',
}


def _format_description_images(markup):
    """Make inline description images conform to the product-detail CSS."""
    def replace(match):
        attrs = match.group(1)
        if not re.search(r'\bwidth\s*=', attrs, re.I):
            attrs += ' width="716"'
        style = re.search(r'\bstyle\s*=\s*(["\'])(.*?)\1', attrs, re.I | re.S)
        if style:
            if 'max-width' not in style.group(2).lower():
                updated = style.group(2).rstrip(';') + '; max-width: 100%;'
                attrs = attrs[:style.start(2)] + updated + attrs[style.end(2):]
        else:
            attrs += ' style="max-width: 100%;"'
        return '<img' + attrs + '>'

    # H5 blocks sometimes contain a complete HTML document; keep only the
    # body so it can be embedded in the existing product-detail page.
    body = re.search(r'<body[^>]*>(.*?)</body>', markup, re.I | re.S)
    markup = body.group(1) if body else markup
    return re.sub(r'<img\b([^>]*)/?>', replace, markup, flags=re.I | re.S)


def _description_section(section_id, title, body):
    return ('<div id="%s" class="section"><div class="title"><span>%s</span></div>'
            '<div class="descrip"><span id="%s-all">%s</span></div></div>') % (
                section_id, html.escape(title), section_id, body)


def _take_first_description_image(markup):
    """Return the first image tag and the markup with that tag removed."""
    match = re.search(r'<img\b[^>]*>', markup, re.I | re.S)
    if not match:
        return '', markup
    image = _format_description_images(match.group(0))
    return image, markup[:match.start()] + markup[match.end():]


def detail_page_url(page):
    """Read the mobile detail-page URL linked from the product page."""
    match = re.search(r'<a\b[^>]*\bid=["\']detail_link["\'][^>]*\bhref=["\']([^"\']+)',
                      page or '', re.I)
    return html.unescape(match.group(1)) if match else ''


def feature_images_from_detail(page):
    """Find every large image between the nine-grid and product text.

    Images in the nine-grid itself are deliberately skipped. Collection stops
    at the first non-empty text node, so later book-excerpt illustrations and
    the final price-note image are excluded.
    """
    section = re.search(r'<section\b[^>]*\bdata-content-name=["\'][^"\']*图书详情[^"\']*["\'][^>]*>(.*?)</section>',
                        page or '', re.I | re.S)
    if not section:
        return []
    content = section.group(1)
    grid_end = re.search(r'<!--\s*九宫格图片\s*结束\s*-->', content, re.S)
    if grid_end:
        content = content[grid_end.end():]
    # Dangdang leaves template/example images in HTML comments. They are not
    # product assets and must not be imported as product-feature images.
    content = re.sub(r'<!--.*?-->', '', content, flags=re.S)
    unique_images = []
    for token in re.findall(r'<img\b[^>]*>|<[^>]+>|[^<]+', content, re.I | re.S):
        image = re.match(r'<img\b[^>]*\bsrc=["\']([^"\']+)', token, re.I | re.S)
        if image:
            image_url = html.unescape(image.group(1))
            if image_url not in unique_images:
                unique_images.append(image_url)
            continue
        if not token.startswith('<') and html.unescape(token).strip():
            break
    return unique_images


def fetch_feature_images(product_page, cookies):
    """Fetch the detail page and return all recommendation-header image URLs."""
    url = detail_page_url(product_page)
    if not url:
        return []
    return feature_images_from_detail(utility.get_html_text(url, cookies=cookies))


def parse_mobile_product(page, feature_images=None):
    """Return product fields in the format expected by the SQL importer.

    Kept public to make page-format changes easy to test without a database.
    """
    data = _load_prd_info(page)
    product = data.get('product_info_new', {}) or {}
    publish = product.get('publish_info', {}) or {}
    price = product.get('new_price', {}) or {}
    product_desc = data.get('product_desc') or product.get('product_desc', {}) or {}
    descriptions = []

    sections_data = data.get('product_desc_sorted') or product.get('product_desc_sorted') or []
    used_ids = set()
    feature_index = None
    # These are populated from detail...html, immediately above 【编辑推荐】.
    # ``beautiful_image`` and ``extract`` contain book-excerpt illustrations.
    if isinstance(feature_images, str):
        feature_images = [feature_images]
    feature_images = feature_images or []
    first_description_image = ''.join(
        '<p>%s</p>' % _format_description_images('<img src="%s">' % image)
        for image in feature_images)
    for section in sections_data:
        if not isinstance(section, dict):
            continue
        name = str(section.get('name', ''))
        if name == '出版信息':
            continue
        content = section.get('content', '')
        if isinstance(content, list):
            content = '<br/>'.join(
                '%s：%s' % (html.escape(str(item.get('name', ''))),
                            html.escape(str(item.get('content', ''))))
                for item in content if isinstance(item, dict))
        if not content:
            continue
        if section.get('format') == 'h5':
            body = _format_description_images(str(content))
        else:
            body = html.escape(str(content)).replace('\n', '<br/>')
        section_id = _SECTION_IDS.get(name, 'feature')
        if section_id in used_ids:
            section_id += '-' + str(len(used_ids) + 1)
        used_ids.add(section_id)
        descriptions.append(_description_section(section_id, name, body))
        if section_id == 'feature':
            feature_index = len(descriptions) - 1

    if first_description_image:
        if feature_index is None:
            descriptions.insert(0, _description_section(
                'feature', '产品特色', '<p>' + first_description_image + '</p>'))
        else:
            marker = '<span id="feature-all">'
            descriptions[feature_index] = descriptions[feature_index].replace(
                marker, marker + '<p>' + first_description_image + '</p>', 1)

    if not descriptions:
        content = product_desc.get('content') or product_desc.get('abstract') or ''
        body = html.escape(str(content)).replace('\n', '<br/>')
        descriptions.append(_description_section('feature', '产品特色', body))

    images = product.get('images_big') or product.get('images') or []
    return {
        'title': str(product.get('product_name', '')).strip(),
        'author': str(publish.get('author_name', '')).strip(),
        'press': str(publish.get('publisher', '')).strip(),
        'isbn': str(publish.get('standard_id', '')).strip(),
        'pressdate': str(publish.get('publish_date', '')).strip(),
        'size': str(publish.get('product_size', '')).strip(),
        'packing': normalize_binding(publish.get('binding', '')),
        'paper': str(publish.get('paper_quality', '')).strip(),
        'shopprice': str(price.get('price_1') or price.get('low_price') or '0.00'),
        'marketprice': str(price.get('price_2') or '0.00'),
        'image': str(images[0]) if images else '',
        'description': '<div><zws-product>%s</zws-product></div>' % ''.join(descriptions),
    }


def _table_names(dbname):
    if dbname == 'zhongw_test':
        return ('ecs_test_goods', 'ecs_test_goods_attr', 'ecs_test_goods_cat',
                'ecs_test_goods_gallery')
    if dbname == 'zhongwenshu_db1':
        return ('ecs_goods', 'ecs_goods_attr', 'ecs_goods_cat', 'ecs_goods_gallery')
    raise ValueError('Unsupported database: %s' % dbname)


def _number(value):
    """Ensure values written into DECIMAL columns are valid SQL decimal strings."""
    try:
        return '%.2f' % float(value)
    except (TypeError, ValueError):
        return '0.00'


def normalize_binding(binding):
    """Map Dangdang's binding text to the predefined ECS attribute options."""
    binding = str(binding or '').strip()
    if re.match(r'.*平装', binding):
        return '平装'
    if re.match(r'.*精装', binding):
        return '精装'
    if re.match(r'.*盒装', binding):
        return '盒装'
    return ''


def _insert_product(connection, dbname, book, image_urls, sn=None):
    goods, goods_attr, goods_cat, goods_gallery = _table_names(dbname)
    sn = sn or generate_sn(book['title'])
    market_price = _number(book['marketprice'])
    shop_price = _number(book['shopprice'])
    attributes = {
        1: book['author'], 2: book['press'], 3: book['isbn'], 4: book['pressdate'],
        5: book['size'], 7: book['packing'], 10: book['paper'],
        232: '¥' + market_price,
    }
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
        cursor.execute(sql, ('134', sn, book['title'],
                             '0',
                             '0.000', '0.00', '0.00',
                             book['description'], image_urls['thumb'], image_urls['goods'], image_urls['ori'],
                             str(int(time.time())),
                             '1'))

        #唯一商品编号
        cursor.execute('SELECT `goods_id` FROM ' + goods + ' WHERE `goods_sn`=%s', sn)
        goods_id = cursor.fetchone()[0]

        #填入书籍信息
        for attr_id, value in attributes.items():
            cursor.execute('INSERT INTO ' + goods_attr +
                           ' (`goods_attr_id`, `goods_id`, `attr_id`, `attr_value`, `attr_price`) '
                           "VALUES (NULL, %s, %s, %s, '0')", (goods_id, attr_id, value))

        #新品到货
        cursor.execute('INSERT INTO ' + goods_cat +
                       " (`goods_id`, `cat_id`) VALUES (%s, '65')", goods_id)

        #填入书籍画册
        if image_urls['galleryori']:
            cursor.execute('INSERT INTO ' + goods_gallery +
                           ' (`img_id`, `goods_id`, `img_url`, `img_desc`, `thumb_url`, `img_original`) '
                           "VALUES (NULL, %s, %s, '', %s, %s)",
                           (goods_id, image_urls['gallerygoods'],
                            image_urls['gallerythumb'], image_urls['galleryori']))
    return goods_id


def _open_image_connection(ftp, dbname):
    result = {'path': ftp[3]}
    if re.match(r'.*your-server\.de$', ftp[0]):
        cls = ftplib.FTP_TLS if ftp[4] == '1' else ftplib.FTP
        result['server'] = cls(ftp[0], ftp[1], ftp[2])
        if ftp[4] == '1':
            result['server'].prot_p()
        result['server'].cwd(('test/' if dbname == 'zhongw_test' else '') + ftp[3])
    elif re.match(r'.*local.*', ftp[0]):
        result['local'] = ftp[0]
    return result


def SpiderToSQL(sqls):
    """Fetch and import the mobile product URLs produced from dangdangConfig.xml."""
    print('Mobile Dangdang spider to SQL start...\n')
    ignored = []
    for host, (username, password, dbname, charset, ftp, urls) in sqls.items():
        connection = pymysql.connect(host=host, user=username, password=password,
                                     database=dbname, charset=charset)
        fconn = _open_image_connection(ftp, dbname)
        try:
            for raw_url, tag in urls.items():
                if tag != 0:
                    continue
                cookies = split_params(raw_url)
                url = remove_params(raw_url)
                webbrowser.open(url)
                page = utility.get_html_text(url, cookies=cookies)
                feature_images = fetch_feature_images(page, cookies)
                book = parse_mobile_product(page, feature_images)
                if not book['title']:
                    print(url + ' not found or page format has changed!')
                    ignored.append(url)
                    continue
                image_sn = generate_sn(book['title'])
                image_urls = save_first_picture(book['image'], image_sn, fconn)
                goods_id = _insert_product(connection, dbname, book, image_urls, image_sn)
                connection.commit()
                print('Imported %s (goods_id=%s)' % (book['title'], goods_id))
        finally:
            connection.close()
            if 'server' in fconn:
                fconn['server'].quit()
    for url in ignored:
        print(url + ' ignored!')
    print('Finished.')


def load_product_urls(config_file='dangdangConfig.xml'):
    """Read product.m product IDs and the optional cookie from dangdangConfig.xml."""
    root = ElementTree.parse(config_file).getroot()
    urls = {}
    for node in root.findall('./http/url'):
        domain = node.get('domain', '').strip()
        if domain != 'product.m.dangdang.com':
            continue
        cookie = node.get('sessionID', '').strip()
        for product_id in node.findall('./productID'):
            product_id = (product_id.text or '').strip()
            if not product_id:
                continue
            url = 'http://%s/%s.html' % (domain, product_id)
            if cookie:
                url += '?sessionID=' + cookie
            urls[url] = 0
    return urls


def load_server_config(config_file='myServerConfig.sxml'):
    """Return the enabled MySQL/FTP connection from the existing server config."""
    root = ElementTree.parse(config_file).getroot()
    active = next((node for node in root if node.get('using') == '1'), None)
    if active is None:
        raise ValueError('No enabled server configuration found')

    def values(parent_name, names):
        parent = active.find(parent_name)
        if parent is None:
            raise ValueError('Missing %s configuration' % parent_name)
        return tuple((parent.findtext(name) or '').strip() for name in names)

    mysql = values('mysql', ('host', 'user', 'password', 'db', 'charset'))
    ftp = values('ftp', ('host', 'user', 'password', 'uploadpath', 'tls'))
    return mysql, ftp


def main(argv=None):
    """Run directly: python MobileSpiderToSQL.py [dangdangConfig.xml] [server.sxml]."""
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) > 2:
        print('Usage: python MobileSpiderToSQL.py [dangdangConfig.xml] [myServerConfig.sxml]')
        return False
    product_config = argv[0] if argv else 'dangdangConfig.xml'
    server_config = argv[1] if len(argv) == 2 else 'myServerConfig.sxml'
    urls = load_product_urls(product_config)
    if not urls:
        print('No product.m.dangdang.com product IDs found in %s' % product_config)
        return False
    mysql, ftp = load_server_config(server_config)
    host, username, password, dbname, charset = mysql
    SpiderToSQL({host: (username, password, dbname, charset, ftp, urls)})
    return True


if __name__ == '__main__':
    main()
