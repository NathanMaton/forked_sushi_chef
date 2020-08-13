#!/usr/bin/env python

from PyPDF2 import PdfFileReader, PdfFileWriter

from ricecooker.chefs import SushiChef
from ricecooker.classes.nodes import TopicNode, VideoNode, DocumentNode
from ricecooker.classes.files import DocumentFile, VideoFile
from ricecooker.classes.licenses import get_license
from ricecooker.utils.pdf import PDFParser

# Scrapping tools
from bs4 import BeautifulSoup
import requests
import os
import json
import youtube_dl
import html

DOWNLOADS_FOLDER = 'chefdata'

# Took page ranges from updated master.
CHANNEL_SPEC = {
    'English':
        {
            'language_code': 'en',
            'pdf_url': 'http://www.pointb.is/s/21CSGuide_English.pdf',
            'video_url': 'http://www.pointb.is/21cs-videos',
            'page_ranges':
                [
                    {'title': 'Introduction', 'page_start': 0, 'page_end': 13},
                    {'title': 'Section 1: Setting a Vision for Your 21st Century Learning Classroom',
                     'page_start': 13, 'page_end': 21},
                    {'title': 'Section 2: 21st Century Mindsets and Practices', 'page_start': 21, 'page_end': 61,
                     'children': [
                         {'title': 'Mindset #1: Mindfulness', 'page_start': 23, 'page_end': 31},
                         {'title': 'Mindset #2: Curiousity', 'page_start': 31, 'page_end': 37},
                         {'title': 'Mindset #3: Growth', 'page_start': 37, 'page_end': 41},
                         {'title': 'Mindset #4: Empathy', 'page_start': 41, 'page_end': 47},
                         {'title': 'Mindset #5: Appreciation', 'page_start': 47, 'page_end': 51},
                         {'title': 'Mindset #6: Experimentation', 'page_start': 51, 'page_end': 57},
                         {'title': 'Mindset #7: Systems Thinking', 'page_start': 57, 'page_end': 61}
                     ]
                     },
                    {'title': 'Section 3: 21st Century Skills', 'page_start': 61, 'page_end': 69},
                    {'title': 'Section 4: Self-Discovery', 'page_start': 69, 'page_end': 95},
                    {'title': 'Section 5: 21st Century Skills Building For Teachers', 'page_start': 95,
                     'page_end': 109},
                    {'title': 'Section 6: Integrating 21st Century Skills Into Your Classroom', 'page_start': 109,
                     'page_end': 135},
                    {'title': 'Thanks To Our Teachers', 'page_start': 135, 'page_end': 137},
                ]

        },
    'Burmese':
        {
            'language_code': 'my',
            'pdf_url': 'http://www.pointb.is/s/21CSGuide_Myanmar.pdf',
            'video_url': 'http://www.pointb.is/21cs-videos-mm',
            'page_ranges':
                [
                    {'title': 'နိဒါန်းအဖွင့်', 'page_start': 0, 'page_end': 13},  # Introduction
                    {'title': '1 - သင်စ် ၂၁ ရာစု စာသင်ခန်းအတွက် မျှော်မှန်းချက်တစ်ခုထားရှိခြင်း', 'page_start': 13,
                     'page_end': 23},  # Section 1
                    {'title': '2 - ၂၁ ရာစု စိတ်နေသဘောထားများနှင့် အလေ့အကျင့်များ', 'page_start': 23, 'page_end': 61,
                     # Section 2
                     'children': [
                         {'title': '#1: စိတ်တည်ငြိမ်မူ သတိအားကောင်းခြင်း', 'page_start': 25, 'page_end': 33},
                         # Mindfulness
                         {'title': '#2: သိလိုစိတ်ပြင်းပြခြင်း', 'page_start': 33, 'page_end': 39},  # Curiousity
                         {'title': '#3: ရှင်သန်ကြီးထွားသောစိတ်', 'page_start': 39, 'page_end': 43},  # Growth
                         {'title': '#4: ကိုယ်ချင်းစာ  နားလည်စိတ်', 'page_start': 43, 'page_end': 49},  # Empathy
                         {'title': '#5: တန်ဖိုးထား ဆက်ဆံခြင်း', 'page_start': 49, 'page_end': 53},  # Appreciation
                         {'title': '#6: လက်တွေ့စမ်းသပ်ဆောင်ရွက်တတ်အောင်', 'page_start': 53, 'page_end': 59},
                         # Experimentation
                         {'title': '#7: စနစ်တစ်ခုလုံးအား ခြုံငုံရဲ စဉ်းစားတွေးခေါ်တတ်အောင်', 'page_start': 59,
                          'page_end': 63}  # Systems Thinking
                     ]
                     },
                    {'title': '3 - စွမ်းဆောင်ရည်မြှင်ရာစုသစ် 21', 'page_start': 63, 'page_end': 75},  # Section 3
                    {'title': '4 - ကိုယ်တိုင်စ် အစွမ်းအစများကို ပြန်လည်ရှာဖွေအကဲဖြတ်ခြင်း', 'page_start': 75,
                     'page_end': 101},  # Section 4
                    {'title': '5 - ဆရာ/ဆရာမများအတွက် စွမ်းရည်များ/ကျွမ်းကျင်မှုများ တည်ဆောက်ပေးခြင်း',
                     'page_start': 101, 'page_end': 117},  # Section 5
                    {'title': '6 - ၂၁ ရာစုခေတ်စွမ်းရည်များကို သင်စ် စာသင်ခန်း ထည့်သွင်းလေ့ကျင့်အသုံးချခြင်း',
                     'page_start': 117, 'page_end': 143},  # Section 6
                    {'title': 'ကျေးဇူးတင်စကား', 'page_start': 143, 'page_end': 145},  # Thanks to our teachers
                ]

        },
}


def download_documents():
    try:
        for idx, key_value_tuple in enumerate(CHANNEL_SPEC.items()):
            language_code = key_value_tuple[1]['language_code']
            pdf_url = key_value_tuple[1]['pdf_url']
            file_path = os.path.join(DOWNLOADS_FOLDER, f'21CSGuide_{language_code}.pdf')
            if os.path.exists(file_path):
                print(f'{pdf_url} already downloaded')
            else:
                response = requests.get(pdf_url)
                with open(file_path, 'wb') as pdf_file:
                    pdf_file.write(response.content)
    except Exception as exc:
        print('Error downloading PDFs: ', exc)


def get_dimensions(pdfin1):
    """
    Get dimensions of second page in PDF file `pdfin1`.
    Returns tuple: (half_width, full_height)
    """
    page = pdfin1.getPage(2)
    double_page_width = page.mediaBox.getUpperRight_x()
    page_width = double_page_width / 2
    page_height = page.mediaBox.getUpperRight_y()
    return page_width, page_height


def split_left_right_pages(pdfin_path, pdfout_path):
    """
    Splits the left and right halves of a page into separate pages.
    """
    pdfin1 = PdfFileReader(open(pdfin_path, 'rb'))  # used for left pages
    pdfin2 = PdfFileReader(open(pdfin_path, 'rb'))  # used for right pages
    pdfout = PdfFileWriter()

    page_width, page_height = get_dimensions(pdfin1)

    num_pages = pdfin1.getNumPages()
    for page_num in range(0, num_pages):
        left_page = pdfin1.getPage(page_num)
        this_width = left_page.mediaBox.getUpperRight_x()

        if this_width > float(page_width) + 20:
            # print(page_num, 'wide')

            left_page = pdfin1.getPage(page_num)
            left_page.cropBox.upperRight = (page_width, page_height)
            left_page.trimBox.upperRight = (page_width, page_height)
            pdfout.addPage(left_page)

            right_page = pdfin2.getPage(page_num)
            right_page.cropBox.lowerLeft = (page_width, 0)
            right_page.trimBox.lowerLeft = (page_width, 0)
            pdfout.addPage(right_page)

        else:
            # print(page_num, 'normal')
            pdfout.addPage(left_page)

    # save outpout PDF result
    with open(pdfout_path, "wb") as out_f:
        pdfout.write(out_f)


def crop_documents():
    for idx, key_value_tuple in enumerate(CHANNEL_SPEC.items()):
        language_code = key_value_tuple[1]['language_code']
        # pdf_url = key_value_tuple[1]['pdf_url']
        file_path = os.path.join(DOWNLOADS_FOLDER, f'21CSGuide_{language_code}.pdf')
        pdf_file_path_out = file_path.replace('.pdf', '_converted.pdf')
        if os.path.exists(pdf_file_path_out):
            print(f'pdfs {language_code} already cropped')
        else:
            split_left_right_pages(file_path, pdf_file_path_out)


def split_pdfs(spec_lang_code):
    language_code = CHANNEL_SPEC[spec_lang_code]['language_code']
    page_ranges = CHANNEL_SPEC[spec_lang_code]['page_ranges']
    file_path = os.path.join(DOWNLOADS_FOLDER, f'21CSGuide_{language_code}_converted.pdf')

    if os.path.exists(file_path):
        print(f'found file at {file_path}, splitting pdf')
        with PDFParser(file_path) as pdfparser:
            chapters = pdfparser.split_subchapters(jsondata=page_ranges)
    else:
        print(f'pdf not found at {file_path}')
    return chapters


def get_video_data():
    try:
        results_dict = {}
        for idx, key_value_tuple in enumerate(CHANNEL_SPEC.items()):

            scraped_urls_list, descriptions_list = [], []
            language_code = key_value_tuple[1]['language_code']
            results_dict[language_code] = {}
            url = key_value_tuple[1]['video_url']
            response = requests.get(url)
            page = BeautifulSoup(response.text, 'html5lib')
            content_divs = page.find_all('div', class_='content-inner')
            num_of_videos = len(content_divs)

            for content_div in content_divs:
                video_block = content_div.find('div', class_='video-block')
                video_wrapper = video_block.find('div', class_='sqs-video-wrapper')
                data_html_raw = video_wrapper['data-html']
                data_html = html.unescape(data_html_raw)
                chunk = BeautifulSoup(data_html, 'html5lib')
                iframe = chunk.find('iframe')
                scraped_urls_list.append((iframe['src']))

                description_area = content_div.find_all('div', class_='sqs-block html-block sqs-block-html')
                description_dirty_content = description_area[1].find('div', class_='sqs-block-content')
                clean_description = description_dirty_content.get_text(" ", strip=True)
                descriptions_list.append(clean_description)

            results_dict[language_code]['urls'] = scraped_urls_list
            results_dict[language_code]['descriptions'] = descriptions_list

        scraped_urls_path = os.path.join(DOWNLOADS_FOLDER, 'scraped_video_urls.json')
        with open(scraped_urls_path, 'w') as fp:
            json.dump(results_dict, fp)

    except Exception as exc:
        print('Error scrapping video urls: ', exc)


def download_videos(topic, language):
    scraped_video_urls_path = os.path.join(DOWNLOADS_FOLDER, 'scraped_video_urls.json')
    with open(scraped_video_urls_path) as f:
        scraped_video_urls = json.load(f)

    video_urls_list = scraped_video_urls[language]['urls']
    video_descriptions_list = scraped_video_urls[language]['descriptions']

    nodes = []
    for video_num, video_url in enumerate(video_urls_list):
        ydl_options = {
            'outtmpl': f'downloads/videos/{video_num}_{language}.%(ext)s',  # uses output templates, see documentation
            'writethumbnail': False,
            'no_warnings': True,
            'continuedl': False,
            'restrictfilenames': True,
            'quiet': False,
            'format': "bestvideo[height<=480][ext=mp4]+bestaudio[ext=m4a]/best[height<=480][ext=mp4]",
            # Note the format specification is important so we get mp4 and not taller than 480
        }

        with youtube_dl.YoutubeDL(ydl_options) as ydl:
            try:
                ydl.add_default_info_extractors()
                vinfo = ydl.extract_info(video_url, download=True)
            except (
                    youtube_dl.utils.DownloadError, youtube_dl.utils.ContentTooShortError,
                    youtube_dl.utils.ExtractorError) as e:
                print('error_occured')

        ext_p1 = vinfo['requested_formats'][0]['format_id']
        ext_p2 = vinfo['requested_formats'][0]['ext']
        video_path = f'downloads/videos/{video_num}_{language}.f{ext_p1}.{ext_p2}'
        video_node = VideoNode(
            source_id=vinfo['webpage_url'],
            title=vinfo['title'],
            description=video_descriptions_list[video_num],
            # aggregator=LE,
            thumbnail=vinfo['thumbnail'],
            license=get_license('CC BY', copyright_holder='NC-SA 4.0'),
            # role=roles.COACH,
            files=[
                VideoFile(
                    path=video_path,
                    language=language
                )
            ])

        topic.add_child(video_node)
    return topic


def add_documents(topic, chapters, language):
    for idx, chapter in enumerate(chapters):
        # if chapter has 'children'
        if 'children' in chapter.keys():
            doc_title = chapter['title']
            child_topic_node = TopicNode(title=doc_title,
                                         source_id=language + doc_title,
                                         thumbnail=DOWNLOADS_FOLDER + '/thumbnail.png')
            for child in chapter['children']:
                child_doc_title = child['title']
                doc_node = DocumentNode(
                    title=child_doc_title,
                    description=f'Chapter {idx} from {doc_title}',
                    source_id=language + child_doc_title,
                    license=get_license('CC BY', copyright_holder='NC-SA 4.0'),
                    language=language,
                    thumbnail=DOWNLOADS_FOLDER + '/thumbnail.png',
                    files=[DocumentFile(path=child['path'],
                                        language=language)],
                )
                child_topic_node.add_child(doc_node)
            topic.add_child(child_topic_node)
        else:
            doc_title = chapter['title']
            doc_node = DocumentNode(
                title=doc_title,
                description=f'Chapter {idx} from 21ST CENTURY GUIDE',
                source_id=language + doc_title,
                license=get_license('CC BY', copyright_holder='NC-SA 4.0'),
                language=language,
                thumbnail=DOWNLOADS_FOLDER + '/thumbnail.png',
                files=[DocumentFile(path=chapter['path'],
                                    language=language)],
            )
            topic.add_child(doc_node)


class PointBChef(SushiChef):
    channel_info = {
        'CHANNEL_TITLE': 'PointB 21CS Guide',
        'CHANNEL_SOURCE_DOMAIN': 'http://www.pointb.is',  # where you got the content (change me!!)
        'CHANNEL_SOURCE_ID': 'nm_21csguide',  # channel's unique id (change me!!)
        'CHANNEL_LANGUAGE': 'mul',  # le_utils language code
        'CHANNEL_THUMBNAIL': DOWNLOADS_FOLDER + '/thumbnail.png',
        'CHANNEL_DESCRIPTION': 'Guide to becoming a 21st teacher',  # (optional)
    }

    def construct_channel(self, **kwargs):

        # these 2 methods output to the downloads folder
        download_documents()
        crop_documents()
        en_chapters = split_pdfs('English')
        my_chapters = split_pdfs('Burmese')

        channel = self.get_channel(**kwargs)
        main_topic_en = TopicNode(title="21ST CENTURY GUIDE English Topic",
                                  source_id="main_en",
                                  thumbnail=DOWNLOADS_FOLDER + '/thumbnail.png')
        topic_videos_en = TopicNode(title="Videos",
                                    source_id="pointb_en_videos",
                                    thumbnail = DOWNLOADS_FOLDER + '/videothumbnail.png')

        main_topic_my = TopicNode(title="21ST CENTURY GUIDE Burmese Topic",
                                  source_id="main_my",
                                  thumbnail=DOWNLOADS_FOLDER + '/thumbnail.png')
        topic_videos_my = TopicNode(title="Videos",
                                    source_id="pointb_my_videos",
                                    thumbnail = DOWNLOADS_FOLDER + '/videothumbnail.png')
        add_documents(main_topic_en, en_chapters, 'en')
        add_documents(main_topic_my, my_chapters, 'my')
        channel.add_child(main_topic_en)
        channel.add_child(main_topic_my)

        topic_videos_en = download_videos(topic_videos_en, 'en')
        topic_videos_my = download_videos(topic_videos_my, 'my')
        channel.add_child(topic_videos_en)
        channel.add_child(topic_videos_my)

        return channel


if __name__ == '__main__':
    """
    Run this script on the command line using:
        python sushichef.py -v --reset --token=YOURTOKENHERE9139139f3a23232
    """
    chef = PointBChef()
    chef.main()
