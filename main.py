from google import genai
from google.genai import types
from dotenv import load_dotenv
from crawling import open_readandtalk, StudentInfo
from report import create_learning_report
import os
from pathlib import Path
load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_KEY"))

def generate_comment(student_info : StudentInfo) -> str:
    prompt = f"""
    <Role>
    You are an experienced English teacher, who carefully uses data and experience to guide students.
    </Role>

    <Task>
    You are given information about a student. Generate one paragraph of teacher comments on this student's performance.
    First, write an overall review of the performance, focusing on the Quiz scores.
    Second, point out some areas where this student could improve.
    </Task>

    <Student Data>
    {student_info.model_dump_json()}
    </Student Data>

    <Info>
    "GR1": "문장형식, 동사용법",
    "GR2": "수, 시제, 태, 병렬구조",
    "GR3": "준동사, 명사구, 형용사구, 부사구",
    "GR4": "명사절, 형용사절, 부사절",
    "GR5": "가정법, 분사구문, 특수구문, 기타"
    </Info>
    
    <Rules>
    1. Only output in Korean.
    2. Do not make up facts.
    </Rules>

    <Example>   
    1. 연조는 다독 마빈을 2권 남겨두고 있고, 정독 8단계를 퀴즈값 평균 90점으로 잘 마무리짓고 정독 9-1 학습에 들어갔습니다. 8단계 학습까지 큰 산을 넘었기에 이제 정독학습은 쓱쓱 잘 해냅니다. 문법은 RG 7단계로 정독단계를 넘어서 학습하고 있습니다. 하루에 2페이지 숙제를 당연하게 생각하고 성실하게 해오니까 문법 진도가 빠릅니다. 이달에는 중고등 VOCA 3-5단계를 클래스카드로 반복학습해서 보다 수준높은 어휘를 공부중입니다. 연조가 단어에 시간소모를 많이 하고 어려워하기도 하는데 클래스카드로 3일정도 다양하게 반복하니까 잘 받아들이는 것 같습니다. 
    2.  예린이는 정독 6단계를 퀴즈값 84점으로 마무리짓고 정독 7단계에 진입하여 학습중입니다. 다독 Fly Guy 시리즈도 퀴즈값 74점으로 마치고, Froggy 시리즈를 학습하고 있습니다. 문법은 어느새 RG 5를 공부하고 있습니다. 단계가 높아졌음에도 리뷰학습까지 하루에 한 권학습을 꼬박꼬박 해내는 것을 보면 갈수록 예린이가 학습에 대한 몰입이 좋아지고 자기주도 학습을 잘 해낸다는 것을 알 수 있습니다. 지난달엔 Fly Guy로 다독을 처음 경험해서 적응기간을 거쳤는데 Froggy는 적응이 완료되어 스토리를 이해하면서 읽는 것이 보입니다.
    3. 리율이는 정독 5단계와  문법 RG 3를 학습중입니다. 개학하고 여러모로 피곤해서인지 리율이는 이달에 학습의 편차가 심했습니다. 학습속도는 리안이와 비슷하거나 오히려 조금 빠르지만 퀴즈값은 평균 10점 가까이 차이가 나고 학습레포트를 보면 학습과정에서 집중하기 어려워했음을 알 수 있습니다. 컨디션과 기분에 영향을 많이 받는 것 같아서 조금 안타깝습니다. 한번 등원할 때마다 문법숙제를 딱 2페이지만 해오게하는데 학교에서 휘리릭해오다보니 오답이 많고 내용숙지도 어려워합니다. 되도록 가정에서 숙제를 할 수 있게 시간과 환경조성을 도와주시면 큰 도움이 될 것 같습니다. 
    </Example>
    
    """
    response = client.models.generate_content(
        model = "gemini-2.0-flash",
        contents = prompt,
        config=types.GenerateContentConfig(temperature=0.3)
    )
    return response.text

if __name__ == "__main__":
    student_infos: list[StudentInfo] = open_readandtalk()
    reports_dir = Path.cwd() / "reports"
    reports_dir.mkdir(exist_ok=True)

    for student_info in student_infos:
        comment = generate_comment(student_info)
        create_learning_report(student_info, comment, dir = reports_dir)


