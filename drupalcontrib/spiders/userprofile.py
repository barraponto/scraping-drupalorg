# -*- coding: utf-8 -*-
import scrapy
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from drupalcontrib.items import DrupalcontribItemLoader


class UserprofileSpider(CrawlSpider):
    name = 'userprofile'
    allowed_domains = ['drupal.org']
    user_search_url = 'https://www.drupal.org/search/user/{username}'

    rules = (
        Rule(LinkExtractor(restrict_css='#block-system-main .pager-next'),
             callback='parse_start_url', follow=True),
        Rule(LinkExtractor(restrict_css='#block-system-main tbody tr td:nth-child(2)'),
             callback='parse_post', follow=False)
    )

    def __init__(self, username=None, *args, **kwargs):
        super(UserprofileSpider, self).__init__(*args, **kwargs)
        if username is None:
            username = raw_input('Please enter username for drupal.org login: ')
        self.username = username

    def start_requests(self):
        yield scrapy.Request(
            self.user_search_url.format(username=self.username),
            callback=self.get_user)

    def get_user(self, response):
        for result in response.css('.search-results .search-result .title a'):
            if result.css('::text').extract_first() == self.username:
                user_link = result.css('::attr("href")').extract_first()
                yield scrapy.Request(response.urljoin(user_link),
                                     callback=self.get_user_content)

    def get_user_content(self, response):
        posts_link = response.css(
            '#nav-content .posts a::attr("href")').extract_first()
        commits_link = response.css(
            '#nav-content .commits a::attr("href")').extract_first()

        return [scrapy.Request(response.urljoin(posts_link)),
                scrapy.Request(response.urljoin(commits_link))]

    def parse_start_url(self, response):
        for row in response.css('.page-user-track-code .views-row'):
            loader = DrupalcontribItemLoader(selector=row)
            loader.add_value('contribution_type', 'commit')
            loader.add_value('author', self.username)
            loader.add_css('project', 'h3 a:first-child::attr("href")')
            loader.add_css('commit', '.commit-info a::attr("href")')
            loader.add_css('date', 'h3 a:nth-child(2)::text')
            loader.add_css('issue', '.views-field-message a::attr("href")')
            yield loader.load_item()

    def parse_post(self, response):
        if response.css('body.node-type-project-issue'):
            loader = DrupalcontribItemLoader(response=response)
            loader.add_value('contribution_type', 'issue')
            loader.add_value('issue', response.url)
            loader.add_css('title', '#page-subtitle')
            loader.add_css('author', '.field-name-project-issue-created-by .field-item a::text')
            loader.add_css('project', '.active.core a::attr("href"), .breadcrumb a:first-child[href^="/project"]::attr("href")')
            loader.add_css('date', '.field-name-project-issue-created .field-item::text')
            issue = loader.load_item()

            if issue.get('project') is None:
                return

            if issue['author'] == self.username:
                yield issue

            for comment in response.css('section.comments .comment'):
                if comment.css('.nodechanges-file-changes'):
                    loader = DrupalcontribItemLoader(selector=comment, issue=issue)
                    loader.add_value('contribution_type', 'patch')
                    loader.add_css('author', '.submitted a.username::text')
                    loader.add_css('date', '.submitted time::text')
                    loader.add_css('patch', '.nodechanges-file-link .file a::attr("href")')
                    patch =  loader.load_item()
                    if patch.get('author') == self.username:
                        yield patch

            for next_page_link in response.css('#block-system-main .pager-next a::attr("href")').extract():
                yield scrapy.Request(response.urljoin(next_page_link),
                                     callback=self.parse_post)
        else:
            self.log(response.url)
