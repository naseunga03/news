import os
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import feedparser
from google import genai

# 1. 구글 뉴스 RSS 수집
def get_latest_news():
    rss_url = "https://news.google.com/rss/search?q=인공지능+when:1d&hl=ko&gl=KR&ceid=KR:ko"
    feed = feedparser.parse(rss_url)
    
    news_items = []
    for entry in feed.entries[:5]:
        news_items.append(f"제목: {entry.title}\n링크: {entry.link}\n")
    
    return "\n".join(news_items)

# 2. Gemini API를 활용한 요약 생성 (재시도 및 대체 모델 적용)
def summarize_news(news_text):
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    
    prompt = f"""
    다음은 오늘 수집된 주요 뉴스 기사들입니다.
    팀원들에게 브리핑할 수 있도록 주요 핵심 이슈를 정리해 주세요.

    [요구사항]
    1. 전체 내용을 관통하는 '오늘의 핵심 이슈 3줄 요약'을 작성하세요.
    2. 각 요약 항목 아래에 관련 기사 제목과 링크를 첨부하세요.
    3. 가독성 높고 정중한 이메일 리포트 형식으로 작성하세요.

    [뉴스 목록]
    {news_text}
    """
    
    models_to_try = ["gemini-3.8-flash", "gemini-2.5-flash"]
    
    for model_name in models_to_try:
        for attempt in range(3):
            try:
                print(f"[{model_name}] 요약 생성 시도 중... (시도 {attempt + 1}/3)")
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt
                )
                return response.text
            except Exception as e:
                print(f"오류 발생 ({e}), 5초 후 재시도합니다...")
                time.sleep(5)
                
    raise RuntimeError("모든 Gemini 모델 서버가 혼잡하여 요청 처리에 실패했습니다.")

# 3. 이메일 자동 발송 (줄바꿈/공백 제거로 HeaderWriteError 완전 방지)
def send_email(subject, content):
    sender_email = os.getenv("SENDER_EMAIL", "").strip()
    sender_password = os.getenv("SENDER_PASSWORD", "").strip()
    
    # \n 및 \r 완전히 제거
    raw_receivers = os.getenv("RECEIVER_EMAILS", "")
    receiver_emails = [e.strip() for e in raw_receivers.replace('\n', '').replace('\r', '').split(",") if e.strip()]

    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = ", ".join(receiver_emails)
    msg['Subject'] = subject
    
    msg.attach(MIMEText(content, 'plain', 'utf-8'))

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, receiver_emails, msg.as_string())

if __name__ == "__main__":
    print("1. 뉴스 수집 중...")
    news = get_latest_news()
    
    print("2. AI 요약 리포트 생성 중...")
    summary = summarize_news(news)
    
    print("3. 팀원 이메일 발송 중...")
    send_email("[일간 브리핑] 오늘의 주요 AI 뉴스 3줄 요약", summary)
    print("발송 완료!")
