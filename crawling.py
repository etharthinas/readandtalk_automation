from re import S
from playwright.sync_api import sync_playwright, Page
from dotenv import load_dotenv
import os
from pydantic import BaseModel
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

load_dotenv()

MAIN_URL = "https://www.englishplatform.co.kr/elp_login.php"
ADMIN_URL = "https://www.englishplatform.co.kr/adm/member_list.php?teaid=&branid=&sfl=mb_level&stx=3"
REPORT_URL_TEMPLATE = (
    "https://www.englishplatform.co.kr/adm/report_mini.php?mb_date1={date}&mb_id={s_id}"
)


class BasicInfo(BaseModel):
    time_end: str
    time_start: str
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
    # prev_month: int
    total: int

    def __add__(self, other):
        return BookInfo(
            intensive=self.intensive + other.intensive,
            extensive=self.extensive + other.extensive,
            classics=self.classics + other.classics,
            curr_month=self.curr_month + other.curr_month,
            total=self.total + other.total,
        )


class StudyInfo(BaseModel):
    curr_count: int
    curr_rate: int
    # prev_count: int
    # prev_rate: int
    total_count: int
    total_rate: int

    def __add__(self, other):
        return StudyInfo(
            curr_count=self.curr_count + other.curr_count,
            curr_rate=int(
                (self.curr_rate * self.curr_count + other.curr_rate * other.curr_count)
                / (self.curr_count + other.curr_count)
                if self.curr_count + other.curr_count != 0
                else 0
            ),
            total_count=self.total_count + other.total_count,
            total_rate=int(
                (
                    self.total_rate * self.total_count
                    + other.total_rate * other.total_count
                )
                / (self.total_count + other.total_count)
                if self.total_count + other.total_count != 0
                else 0
            ),
        )


class GR(BaseModel):
    GR_num: str
    right: int
    total: int

class StudentInfo(BaseModel):
    basic_info: BasicInfo | None
    book_info: list[BookInfo, BookInfo]
    word_info: list[StudyInfo, StudyInfo]
    puzzle_info: list[StudyInfo, StudyInfo]
    dictation_info: list[StudyInfo, StudyInfo]
    writing_info: list[StudyInfo, StudyInfo]
    quiz_info: list[StudyInfo, StudyInfo]
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
        for s_id in student_ids:
            try:
                student_infos.append(get_student_info(page, s_id = s_id))
            except Exception as e:
                print(e)
        return student_infos


def get_basic_info(page: Page) -> BasicInfo:
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
        time_end=time,
        time_start="",
        lexile=lexile,
        name=name,
        school=school,
        grade=grade,
        count=count,
        level=level,
    )
    return basic_info


def get_book_info(page: Page, current: bool = False) -> BookInfo:
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

    # prev_month_locator = "#chart_div1 svg > g:nth-of-type(3) > g:nth-of-type(1) > g:nth-of-type(2) rect:nth-of-type(1)[x='200']"
    # if page.locator(prev_month_locator).get_attribute("height") == "0.5":
    #     prev_month = 0
    # else:
    #     page.click(prev_month_locator)
    #     page.wait_for_timeout(500)
    #     try:
    #         prev_month = int(
    #             page.locator("#chart_div1 > div > div[aria-hidden='true']").inner_text()
    #         )
    #     except Exception:
    #         prev_month = 0

    if current:
        total = int(
            book_table.locator("tr")
            .nth(1)
            .locator("td")
            .nth(5)
            .inner_text()
            .split(" ")[1]
            .split("권")[0]
        )
    else:
        total = 0

    book_info = BookInfo(
        intensive=intensive,
        extensive=extensive,
        classics=classics,
        curr_month=curr_month,
        # prev_month=prev_month,
        total=total,
    )
    return book_info


def get_word_info(page: Page, current: bool = False) -> StudyInfo:
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
    # prev_count = int(
    #     word_table.locator("tr")
    #     .nth(1)
    #     .locator("td")
    #     .nth(2)
    #     .inner_text()
    #     .split("개")[0]
    #     .replace(",", "")
    # )
    # prev_rate = int(
    #     word_table.locator("tr").nth(1).locator("td").nth(3).inner_text().split("%")[0]
    # )

    if current:
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
            word_table.locator("tr")
            .nth(1)
            .locator("td")
            .nth(5)
            .inner_text()
            .split("%")[0]
        )
    else:
        total_count, total_rate = 0, 0

    word_info = StudyInfo(
        curr_count=curr_count,
        curr_rate=curr_rate,
        # prev_count=prev_count,
        # prev_rate=prev_rate,
        total_count=total_count,
        total_rate=total_rate,
    )
    return word_info


def get_puzzle_info(page: Page, current: bool = False) -> StudyInfo:
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
    # prev_count = int(
    #     puzzle_table.locator("tr")
    #     .nth(1)
    #     .locator("td")
    #     .nth(2)
    #     .inner_text()
    #     .split("개")[0]
    #     .replace(",", "")
    # )
    # prev_rate = int(
    #     puzzle_table.locator("tr")
    #     .nth(1)
    #     .locator("td")
    #     .nth(3)
    #     .inner_text()
    #     .split("%")[0]
    # )

    if current:
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
    else:
        total_count, total_rate = 0, 0

    puzzle_info = StudyInfo(
        curr_count=curr_count,
        curr_rate=curr_rate,
        # prev_count=prev_count,
        # prev_rate=prev_rate,
        total_count=total_count,
        total_rate=total_rate,
    )
    return puzzle_info


def get_dictation_info(page: Page, current: bool = False) -> StudyInfo:
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
    # prev_count = int(
    #     dictation_table.locator("tr")
    #     .nth(1)
    #     .locator("td")
    #     .nth(2)
    #     .inner_text()
    #     .split("개")[0]
    #     .replace(",", "")
    # )
    # prev_rate = int(
    #     dictation_table.locator("tr")
    #     .nth(1)
    #     .locator("td")
    #     .nth(3)
    #     .inner_text()
    #     .split("%")[0]
    # )

    if current:
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
    else:
        total_count, total_rate = 0, 0

    dictation_info = StudyInfo(
        curr_count=curr_count,
        curr_rate=curr_rate,
        # prev_count=prev_count,
        # prev_rate=prev_rate,
        total_count=total_count,
        total_rate=total_rate,
    )
    return dictation_info


def get_writing_info(page: Page, current: bool = False) -> StudyInfo:
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
    # prev_count = int(
    #     writing_table.locator("tr")
    #     .nth(1)
    #     .locator("td")
    #     .nth(2)
    #     .inner_text()
    #     .split("개")[0]
    #     .replace(",", "")
    # )
    # prev_rate = int(
    #     writing_table.locator("tr")
    #     .nth(1)
    #     .locator("td")
    #     .nth(3)
    #     .inner_text()
    #     .split("%")[0]
    # )

    if current:
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
    else:
        total_count, total_rate = 0, 0

    writing_info = StudyInfo(
        curr_count=curr_count,
        curr_rate=curr_rate,
        # prev_count=prev_count,
        # prev_rate=prev_rate,
        total_count=total_count,
        total_rate=total_rate,
    )
    return writing_info


def get_quiz_info(page: Page, current: bool = False) -> StudyInfo:
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
    # prev_count = int(
    #     quiz_table.locator("tr")
    #     .nth(1)
    #     .locator("td")
    #     .nth(2)
    #     .inner_text()
    #     .split("개")[0]
    #     .replace(",", "")
    # )
    # prev_rate = int(
    #     quiz_table.locator("tr").nth(1).locator("td").nth(3).inner_text().split("%")[0]
    # )

    if current:
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
            quiz_table.locator("tr")
            .nth(1)
            .locator("td")
            .nth(5)
            .inner_text()
            .split("%")[0]
        )
    else:
        total_count, total_rate = 0, 0

    quiz_info = StudyInfo(
        curr_count=curr_count,
        curr_rate=curr_rate,
        # prev_count=prev_count,
        # prev_rate=prev_rate,
        total_count=total_count,
        total_rate=total_rate,
    )
    return quiz_info

def get_gr_info(page: Page) -> list[GR]:
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
    return [
        GR(GR_num="GR1", right=GR1[0], total=GR1[1]),
        GR(GR_num="GR2", right=GR2[0], total=GR2[1]),
        GR(GR_num="GR3", right=GR3[0], total=GR3[1]),
        GR(GR_num="GR4", right=GR4[0], total=GR4[1]),
        GR(GR_num="GR5", right=GR5[0], total=GR5[1]),
    ]

def get_student_info(
    page: Page, s_id: str
) -> StudentInfo:

    basic_info = None
    gr_list = None

    book_infos_curr = []
    word_infos_curr = []
    puzzle_infos_curr = []
    dictation_infos_curr = []
    writing_infos_curr = []
    quiz_infos_curr = []

    book_infos_prev = []
    word_infos_prev = []
    puzzle_infos_prev = []
    dictation_infos_prev = []
    writing_infos_prev = []
    quiz_infos_prev = []

    current_month = datetime.now() - timedelta(days=7)
    months_list = []
    for i in range(6):
        months_list.append((current_month - relativedelta(months=i)).strftime("%Y%m"))

    for date in months_list[:3]:
        page.goto(REPORT_URL_TEMPLATE.format(date=date, s_id=s_id))
        is_current = (date == current_month.strftime("%Y%m"))

        if is_current:
            basic_info = get_basic_info(page)
            basic_info.time_start = (current_month - relativedelta(months=2)).strftime("%Y%m")
            gr_list = get_gr_info(page)

        book_infos_curr.append(get_book_info(page, is_current))
        word_infos_curr.append(get_word_info(page, is_current))
        puzzle_infos_curr.append(get_puzzle_info(page, is_current))
        dictation_infos_curr.append(get_dictation_info(page, is_current))
        writing_infos_curr.append(get_writing_info(page, is_current))
        quiz_infos_curr.append(get_quiz_info(page, is_current))

    for date in months_list[3:]:
        page.goto(REPORT_URL_TEMPLATE.format(date=date, s_id=s_id))

        book_infos_prev.append(get_book_info(page))
        word_infos_prev.append(get_word_info(page))
        puzzle_infos_prev.append(get_puzzle_info(page))
        dictation_infos_prev.append(get_dictation_info(page))
        writing_infos_prev.append(get_writing_info(page))
        quiz_infos_prev.append(get_quiz_info(page))

    return StudentInfo(
        basic_info=basic_info,
        book_info=[getsum(book_infos_curr), getsum(book_infos_prev)],
        word_info=[getsum(word_infos_curr), getsum(word_infos_prev)],
        puzzle_info=[getsum(puzzle_infos_curr), getsum(puzzle_infos_prev)],
        dictation_info=[getsum(dictation_infos_curr), getsum(dictation_infos_prev)],
        writing_info=[getsum(writing_infos_curr), getsum(writing_infos_prev)],
        quiz_info=[getsum(quiz_infos_curr), getsum(quiz_infos_prev)],
        GR_list=gr_list,
    )

def getsum(list_of_objects):
    if len(list_of_objects) == 0:
        return None
    elif len(list_of_objects) == 1:
        return list_of_objects[0]
    else:
        return list_of_objects[0] + getsum(list_of_objects[1:])

if __name__ == "__main__":
    x = open_readandtalk()
