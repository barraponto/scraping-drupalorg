# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy
import delorean
from scrapy.loader import ItemLoader
from scrapy.loader.processors import MapCompose
from scrapylib.processors import default_input_processor as slp_default_in
from scrapylib.processors import default_output_processor as slp_default_out


def parse_datestring(datestring):
    return delorean.parse(datestring).datetime


class DrupalcontribItem(scrapy.Item):
    contribution_type = scrapy.Field()
    project = scrapy.Field()
    issue = scrapy.Field()
    title = scrapy.Field()
    author = scrapy.Field()
    date = scrapy.Field()
    commit = scrapy.Field()
    patch = scrapy.Field()


class DrupalcontribItemLoader(ItemLoader):
    default_item_class = DrupalcontribItem
    default_input_processor = slp_default_in
    default_output_processor = slp_default_out
    date_in = MapCompose(*(slp_default_in.functions + (parse_datestring,)))

    def __init__(self, issue=None, *args, **kwargs):
        super(DrupalcontribItemLoader, self).__init__(*args, **kwargs)
        if issue:
            self.add_value('issue', issue['issue'])
            self.add_value('project', issue['project'])
