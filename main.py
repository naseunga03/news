import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import feedparser
import google.generativeai as genai

# 1. 구글 뉴스 RSS 수집
def get_latest_news():
    rss_url = "https://news.google.com/rss/search?q=인공지능+when:1d&hl=ko&gl=KR&ceid=KR:ko"
    feed = feedparser.parse(rss_url)
    
    news_items = []
    for entry in feed.entries[:5]:
        news_items.append(f"제목: {entry.title}\n링크: {entry.link}\n")
    
    return "\n".join(news_items)

# 2. Gemini API를 활용한 요약 생성
def summarize_news(news_text):
    # API 키 설정
    api_key = os.getenv("GEMINI_API_KEY")
    genai.configure(api_key=api_key)
    
    # 모델 불러오기
    model = genai.GenerativeModel('gemini-1.5-flash')
    
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
    
    response = model.generate_content(prompt)
    return response.text

# 3. 이메일 자동 발송
def send_email(subject, content):
    sender_email = os.getenv("SENDER_EMAIL")
    sender_password = os.getenv("SENDER_PASSWORD")
    receiver_emails = [e.strip() for e in os.getenv("RECEIVER_EMAILS").split(",")]

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
