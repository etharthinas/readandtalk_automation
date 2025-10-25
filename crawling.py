from re import S
from playwright.sync_api import sync_playwright, Page
from dotenv import load_dotenv
import os
from pydantic import BaseModel
from datetime import datetime

load_dotenv()

MAIN_URL = "https://www.readandtalk.co.kr/elp_login.php"
ADMIN_URL = "https://www.readandtalk.co.kr/adm/member_list.php?teaid=&branid=&sfl=mb_level&stx=3"
REPORT_URL_TEMPLATE = "https://www.readandtalk.co.kr/adm/report_mini.php?mb_id={s_id}"


class BasicInfo(BaseModel):
    time: str
    lexile: int
    name: str
    school: str
    grade: int
    count: int
    level: str


class BookInfo(BaseModel):
    intensive: int
    extensive: int
    classics: int
    curr_month: int
    prev_month: int
    total: int


class WordInfo(BaseModel):
    curr_count: int
    curr_rate: int
    prev_count: int
    prev_rate: int
    total_count: int
    total_rate: int


class PuzzleInfo(BaseModel):
    curr_count: int
    curr_rate: int
    prev_count: int
    prev_rate: int
    total_count: int
    total_rate: int


class DictationInfo(BaseModel):
    curr_count: int
    curr_rate: int
    prev_count: int
    prev_rate: int
    total_count: int
    total_rate: int


class WritingInfo(BaseModel):
    curr_count: int
    curr_rate: int
    prev_count: int
    prev_rate: int
    total_count: int
    total_rate: int


class QuizInfo(BaseModel):
    curr_count: int
    curr_rate: int
    prev_count: int
    prev_rate: int
    total_count: int
    total_rate: int


class GR(BaseModel):
    GR_num: str
    right: int
    total: int


class StudentInfo(BaseModel):
    basic_info: BasicInfo
    book_info: BookInfo
    word_info: WordInfo
    puzzle_info: PuzzleInfo
    dictation_info: DictationInfo
    writing_info: WritingInfo
    quiz_info: QuizInfo
    GR_list: list[GR]


def open_readandtalk() -> list[StudentInfo]:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        page.goto(MAIN_URL)

        # LOGIN
        input_id = page.locator("input.the-signin-account")
        input_pw = page.locator("input.the-signin-password")
        login_btn = page.locator("#normal-login")

        input_id.fill(os.getenv("READANDTALK_ID"))
        input_pw.fill(os.getenv("READANDTALK_PW"))
        login_btn.click()

        page.wait_for_load_state("load")

        page.goto(ADMIN_URL)

        # GET LIST
        student_ids = []

        student_infos = list()
        student_list = page.locator("tbody > tr td[headers='mb_list_id']").all()

        for student in student_list:
            student_ids.append(student.inner_text())

        # ITERATE TO GET REPORTS
        for s_id in student_ids[0:1]:
            try:
                student_infos.append(get_student_info(page, s_id))
            except Exception as e:
                print(e)
        return student_infos


def get_student_info(page: Page, s_id: str) -> StudentInfo:
    page.goto(REPORT_URL_TEMPLATE.format(s_id=s_id))

    # Basic Info
    basic_table = page.locator("#print > table").nth(1)
    time = basic_table.locator("tr").locator("td").nth(1).inner_text()
    lexile = int(
        basic_table.locator("tr").locator("td").nth(4).inner_text().split("L")[0]
    )

    student_table = page.locator("#print > table").nth(2)
    name = student_table.locator("tr").nth(0).locator("td").nth(1).inner_text()
    school = student_table.locator("tr").nth(0).locator("td").nth(3).inner_text()
    grade = int(student_table.locator("tr").nth(0).locator("td").nth(5).inner_text())
    count = int(student_table.locator("tr").nth(1).locator("td").nth(1).inner_text())
    level = student_table.locator("tr").nth(1).locator("td").nth(3).inner_text()

    basic_info = BasicInfo(
        time=time,
        lexile=lexile,
        name=name,
        school=school,
        grade=grade,
        count=count,
        level=level,
    )

    # Book Info
    book_table = page.locator("#print > table").nth(3)
    intensive = int(
        book_table.locator("tr")
        .nth(1)
        .locator("td")
        .nth(0)
        .inner_text()
        .split(" ")[1]
        .split("권")[0]
        .replace(",", "")
    )
    extensive = int(
        book_table.locator("tr")
        .nth(1)
        .locator("td")
        .nth(1)
        .inner_text()
        .split(" ")[1]
        .split("권")[0]
        .replace(",", "")
    )
    classics = int(
        book_table.locator("tr")
        .nth(1)
        .locator("td")
        .nth(3)
        .inner_text()
        .split(" ")[1]
        .split("권")[0]
        .replace(",", "")
    )
    curr_month = int(
        book_table.locator("tr")
        .nth(1)
        .locator("td")
        .nth(4)
        .inner_text()
        .split(" ")[1]
        .split("권")[0]
    )

    prev_month_locator = "#chart_div1 svg > g:nth-of-type(3) > g:nth-of-type(1) > g:nth-of-type(2) rect:nth-of-type(1)[x='200']"
    if page.locator(prev_month_locator).get_attribute("height") == "0.5":
        prev_month = 0
    else:
        page.click(prev_month_locator)
        page.wait_for_timeout(500)
        try:
            prev_month = int(
                page.locator("#chart_div1 > div > div[aria-hidden='true']").inner_text()
            )
        except Exception:
            prev_month = 0
    total = int(
        book_table.locator("tr")
        .nth(1)
        .locator("td")
        .nth(5)
        .inner_text()
        .split(" ")[1]
        .split("권")[0]
    )

    book_info = BookInfo(
        intensive=intensive,
        extensive=extensive,
        classics=classics,
        curr_month=curr_month,
        prev_month=prev_month,
        total=total,
    )

    # Word Info
    word_table = page.locator("#print > table").nth(5)
    curr_count = int(
        word_table.locator("tr")
        .nth(1)
        .locator("td")
        .nth(0)
        .inner_text()
        .split("개")[0]
        .replace(",", "")
    )
    curr_rate = int(
        word_table.locator("tr").nth(1).locator("td").nth(1).inner_text().split("%")[0]
    )
    prev_count = int(
        word_table.locator("tr")
        .nth(1)
        .locator("td")
        .nth(2)
        .inner_text()
        .split("개")[0]
        .replace(",", "")
    )
    prev_rate = int(
        word_table.locator("tr").nth(1).locator("td").nth(3).inner_text().split("%")[0]
    )
    total_count = int(
        word_table.locator("tr")
        .nth(1)
        .locator("td")
        .nth(4)
        .inner_text()
        .split("개")[0]
        .replace(",", "")
    )
    total_rate = int(
        word_table.locator("tr").nth(1).locator("td").nth(5).inner_text().split("%")[0]
    )

    word_info = WordInfo(
        curr_count=curr_count,
        curr_rate=curr_rate,
        prev_count=prev_count,
        prev_rate=prev_rate,
        total_count=total_count,
        total_rate=total_rate,
    )

    # Puzzle Info
    puzzle_table = page.locator("#print > table").nth(7)
    curr_count = int(
        puzzle_table.locator("tr")
        .nth(1)
        .locator("td")
        .nth(0)
        .inner_text()
        .split("개")[0]
        .replace(",", "")
    )
    curr_rate = int(
        puzzle_table.locator("tr")
        .nth(1)
        .locator("td")
        .nth(1)
        .inner_text()
        .split("%")[0]
    )
    prev_count = int(
        puzzle_table.locator("tr")
        .nth(1)
        .locator("td")
        .nth(2)
        .inner_text()
        .split("개")[0]
        .replace(",", "")
    )
    prev_rate = int(
        puzzle_table.locator("tr")
        .nth(1)
        .locator("td")
        .nth(3)
        .inner_text()
        .split("%")[0]
    )
    total_count = int(
        puzzle_table.locator("tr")
        .nth(1)
        .locator("td")
        .nth(4)
        .inner_text()
        .split("개")[0]
        .replace(",", "")
    )
    total_rate = int(
        puzzle_table.locator("tr")
        .nth(1)
        .locator("td")
        .nth(5)
        .inner_text()
        .split("%")[0]
    )

    puzzle_info = PuzzleInfo(
        curr_count=curr_count,
        curr_rate=curr_rate,
        prev_count=prev_count,
        prev_rate=prev_rate,
        total_count=total_count,
        total_rate=total_rate,
    )

    # Dication Info
    dictation_table = page.locator("#print > table").nth(9)
    curr_count = int(
        dictation_table.locator("tr")
        .nth(1)
        .locator("td")
        .nth(0)
        .inner_text()
        .split("개")[0]
        .replace(",", "")
    )
    curr_rate = int(
        dictation_table.locator("tr")
        .nth(1)
        .locator("td")
        .nth(1)
        .inner_text()
        .split("%")[0]
    )
    prev_count = int(
        dictation_table.locator("tr")
        .nth(1)
        .locator("td")
        .nth(2)
        .inner_text()
        .split("개")[0]
        .replace(",", "")
    )
    prev_rate = int(
        dictation_table.locator("tr")
        .nth(1)
        .locator("td")
        .nth(3)
        .inner_text()
        .split("%")[0]
    )
    total_count = int(
        dictation_table.locator("tr")
        .nth(1)
        .locator("td")
        .nth(4)
        .inner_text()
        .split("개")[0]
        .replace(",", "")
    )
    total_rate = int(
        dictation_table.locator("tr")
        .nth(1)
        .locator("td")
        .nth(5)
        .inner_text()
        .split("%")[0]
    )

    dictation_info = DictationInfo(
        curr_count=curr_count,
        curr_rate=curr_rate,
        prev_count=prev_count,
        prev_rate=prev_rate,
        total_count=total_count,
        total_rate=total_rate,
    )

    # Writing Info
    writing_table = page.locator("#print > table").nth(11)
    curr_count = int(
        writing_table.locator("tr")
        .nth(1)
        .locator("td")
        .nth(0)
        .inner_text()
        .split("개")[0]
        .replace(",", "")
    )
    curr_rate = int(
        writing_table.locator("tr")
        .nth(1)
        .locator("td")
        .nth(1)
        .inner_text()
        .split("%")[0]
    )
    prev_count = int(
        writing_table.locator("tr")
        .nth(1)
        .locator("td")
        .nth(2)
        .inner_text()
        .split("개")[0]
        .replace(",", "")
    )
    prev_rate = int(
        writing_table.locator("tr")
        .nth(1)
        .locator("td")
        .nth(3)
        .inner_text()
        .split("%")[0]
    )
    total_count = int(
        writing_table.locator("tr")
        .nth(1)
        .locator("td")
        .nth(4)
        .inner_text()
        .split("개")[0]
        .replace(",", "")
    )
    total_rate = int(
        writing_table.locator("tr")
        .nth(1)
        .locator("td")
        .nth(5)
        .inner_text()
        .split("%")[0]
    )

    writing_info = WritingInfo(
        curr_count=curr_count,
        curr_rate=curr_rate,
        prev_count=prev_count,
        prev_rate=prev_rate,
        total_count=total_count,
        total_rate=total_rate,
    )

    # Quiz Info
    quiz_table = page.locator("#print > table").nth(13)
    curr_count = int(
        quiz_table.locator("tr")
        .nth(1)
        .locator("td")
        .nth(0)
        .inner_text()
        .split("개")[0]
        .replace(",", "")
    )
    curr_rate = int(
        quiz_table.locator("tr").nth(1).locator("td").nth(1).inner_text().split("%")[0]
    )
    prev_count = int(
        quiz_table.locator("tr")
        .nth(1)
        .locator("td")
        .nth(2)
        .inner_text()
        .split("개")[0]
        .replace(",", "")
    )
    prev_rate = int(
        quiz_table.locator("tr").nth(1).locator("td").nth(3).inner_text().split("%")[0]
    )
    total_count = int(
        quiz_table.locator("tr")
        .nth(1)
        .locator("td")
        .nth(4)
        .inner_text()
        .split("개")[0]
        .replace(",", "")
    )
    total_rate = int(
        quiz_table.locator("tr").nth(1).locator("td").nth(5).inner_text().split("%")[0]
    )

    quiz_info = QuizInfo(
        curr_count=curr_count,
        curr_rate=curr_rate,
        prev_count=prev_count,
        prev_rate=prev_rate,
        total_count=total_count,
        total_rate=total_rate,
    )

    gr_table = page.locator("#print > table").nth(15)
    GR1 = list(
        map(
            int,
            tuple(
                gr_table.locator("tr")
                .nth(1)
                .locator("td")
                .nth(1)
                .inner_text()
                .split("/")
            ),
        )
    )
    GR2 = list(
        map(
            int,
            tuple(
                gr_table.locator("tr")
                .nth(1)
                .locator("td")
                .nth(3)
                .inner_text()
                .split("/")
            ),
        )
    )
    GR3 = list(
        map(
            int,
            tuple(
                gr_table.locator("tr")
                .nth(1)
                .locator("td")
                .nth(5)
                .inner_text()
                .split("/")
            ),
        )
    )
    GR4 = list(
        map(
            int,
            tuple(
                gr_table.locator("tr")
                .nth(1)
                .locator("td")
                .nth(7)
                .inner_text()
                .split("/")
            ),
        )
    )
    GR5 = list(
        map(
            int,
            tuple(
                gr_table.locator("tr")
                .nth(1)
                .locator("td")
                .nth(9)
                .inner_text()
                .split("/")
            ),
        )
    )

    return StudentInfo(
        basic_info=basic_info,
        book_info=book_info,
        word_info=word_info,
        puzzle_info=puzzle_info,
        dictation_info=dictation_info,
        writing_info=writing_info,
        quiz_info=quiz_info,
        GR_list=[
            GR(GR_num="GR1", right=GR1[0], total=GR1[1]),
            GR(GR_num="GR2", right=GR2[0], total=GR2[1]),
            GR(GR_num="GR3", right=GR3[0], total=GR3[1]),
            GR(GR_num="GR4", right=GR4[0], total=GR4[1]),
            GR(GR_num="GR5", right=GR5[0], total=GR5[1]),
        ],
    )


if __name__ == "__main__":
    open_readandtalk()
