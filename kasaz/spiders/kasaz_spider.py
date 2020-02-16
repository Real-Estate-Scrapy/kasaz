# -*- coding: utf-8 -*-
import json
import re

import scrapy
from bs4 import BeautifulSoup

from ..items import PropertyItem


class KasazSpiderSpider(scrapy.Spider):
    name = 'kasaz_spider'

    def __init__(self, page_url='', url_file=None, *args, **kwargs):
        self.start_urls = ['http://www.kasaz.com/venta-pisos-bajos-aticos-casas-lofts-duplexes-estudios/barcelona']

        if not page_url and url_file is None:
            TypeError('No page URL or URL file passed.')

        if url_file is not None:
            with open(url_file, 'r') as f:
                self.start_urls = f.readlines()
        if page_url:
            # Replaces the list of URLs if url_file is also provided
            self.start_urls = [page_url]

        super().__init__(*args, **kwargs)

    def start_requests(self):
        for page in self.start_urls:
            yield scrapy.Request(url=page, callback=self.crawl_page)

    def crawl_page(self, response):
        json_data_in_str = response.xpath('.//*[@id="init_data"]//@data-search-results').get()
        property_json_list = json.loads(json_data_in_str)['markers']

        property_urls = self.get_property_urls(property_json_list)
        for property_url in property_urls:
            yield scrapy.Request(url=property_url, callback=self.crawl_property)

    def crawl_property(self, response):
        property = PropertyItem()

        # Resource
        property["resource_url"] = "https://www.kasaz.com/"
        property["resource_title"] = 'Kasaz'
        property["resource_country"] = 'ES'

        # Property
        property["active"] = 1
        property["url"] = response.url
        property["title"] = response.xpath('//h1[@class="title"]/text()').get()
        property["subtitle"] = ''
        property["location"] = ''
        property["extra_location"] = ''
        property["body"] = self.get_body(response)

        # Price
        property["current_price"] = response.xpath('//*[@class="price"]//@data-price').get()
        property["original_price"] = response.xpath('//*[@class="price"]//@data-price').get()
        property["price_m2"] = response.xpath('//*[@class="price_per_square_meter"]/text()').re_first('\d+.\d+')
        property["area_market_price"] = response.css('tr:nth-child(2) .guidebox_number').re_first('\d+\.\d+')
        property["square_meters"] = response.xpath('//*[@class="sqm_infos"]/text()').re_first('\s(\d+.*?)m²')

        # Details
        property["area"] = ' / '.join(response.xpath('//ol[@class="breadcrumbs"]').xpath('//*[@class="link"]//text()').getall())
        property["tags"] = self.get_tags(response)
        property["bedrooms"] = response.css('.detail::text').re('\d+')[0]
        property["bathrooms"] = response.css('.detail::text').re('\d+')[1]
        property["last_update"] = ''
        property["certification_status"] = self.get_cert_status(response)
        property["consumption"] = self.get_cert_status(response)
        property["emissions"] = self.get_cert_status(response)

        # Multimedia
        property["main_image_url"] = response.xpath('//*[@class="listing_picture_block"]//@href').get()
        property["image_urls"] = ';'.join(response.xpath('//*[@class="listing_picture_block"]//@href').getall()[1:])
        property["floor_plan"] = ''
        property["energy_certificate"] = ''
        property["video"] = response.css('.video_iframe.media_iframe::attr(src)').get()

        # Agents
        property["seller_type"] = response.xpath('//img[@class="agency_logo_info_box"]//@alt').get()
        property["agent"] = response.xpath('//img[@class="agency_logo_info_box"]//@alt').get()
        property["ref_agent"] = response.xpath('//*[@class="agent_reference"]/text()').re_first('Referencia: (.+)')
        property["source"] = ''
        property["ref_source"] = ''
        property["phone_number"] = response.xpath('//div[@class="phone_number"]/a/text()').re_first('\S.+')

        # Additional
        property["additional_url"] = ''
        property["published"] = ''
        property["scraped_ts"] = ''

        yield property

    def get_property_urls(self, json_list):
        property_url_list = []
        base_href = 'https://www.kasaz.com/'

        for index, property_json in enumerate(json_list):
            id = property_json['id']
            title_slug = self.slugify(property_json['t'])
            property_url = base_href + '/venta-inmueble/{}/{}/'.format(id, title_slug)
            property_url_list.append(property_url)

        return property_url_list

    def slugify(self, title: str) -> str:
        splitted_title = title.lower().split()
        return '-'.join(splitted_title)

    def get_body(self, response):
        body_list = response.xpath('//*[@class="description_text"]//text()').getall()
        body_list = list(map(lambda text: text.strip(), body_list))
        return '\n'.join(body_list)

    def get_tags(self, response):
        tags = ''
        tags_section_blocks = response.xpath('//section[contains(@class, "listing_section")]').getall()
        for tag_section in tags_section_blocks:
            soup = BeautifulSoup(tag_section, 'lxml')
            tags_raw_text = soup.get_text().strip().replace('Detalles', '')
            # Clean-up
            tags_raw_text = re.sub('(\w) ?\n\n {14,}(\w)', r'\1: \2', tags_raw_text)

            # Convert to list
            tags_in_list = tags_raw_text.split("\n")
            tags_in_list = list(filter(lambda tag: re.search('\w+', tag), tags_in_list))
            tags_in_list = list(map(lambda tag: re.search('\w.+', tag).group(), tags_in_list))
            tags += ';'.join(tags_in_list) + ';'

        return tags

    def get_cert_status(self, response):
        heading = response.css('div.energy_efficiency h2::text').re_first('\w.+')
        value = response.css('div.energy_efficiency .listing_property::text').re_first('\w.+')

        return '{}: {}'.format(heading, value)




