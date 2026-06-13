import os
import json
import smtplib
from datetime import date
from email.mime.text import MIMEText
from email.header import Header
import anthropic

# ===== 設定 =====
# リサーチしたいテーマ。自由に足し引きしてください。
RESEARCH_TOPICS = [
    "食べ歩き イベント SNS 集客 成功事例",
    "バルイベント Instagram リール 集客",
    "地方 飲食 イベント 来場者 増やす 施策",
    "ご当地グルメ イベント 若年層 集客 2026",
]

# 自社の文脈。これを渡すと「転用案」の精度が上がります。
OUR_CONTEXT = """
気仙沼バル2026（2026年7月2〜4日、宮城県気仙沼市の食べ歩きイベント、参加36店舗）の
SNS・デジタルマーケティング担当。Instagram運用チームは初心者中心。
主な施策：Meta広告（地元20〜35歳ターゲット）、リール制作、ずんだもん動画。
予算は限られており、低コストで再現できる施策を求めている。
"""

client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])


def research_topic(topic: str) -> str:
    """1テーマぶんのWeb検索＋要約をClaudeに任せる"""
    prompt = f"""あなたは中小企業診断士の視点を持つマーケティング分析者です。
次のテーマについてWeb検索し、最新の事例や施策を調べてください。

テーマ：{topic}

調べた内容を踏まえ、以下の構成で日本語のレポートを書いてください。
出力はそのままメール本文に使うので、前置きや「承知しました」等は不要です。

【テーマ】{topic}
■ 見つかった施策・事例（2〜4個、出典の媒体名を添える）
■ なぜ効果が出たと考えられるか（簡潔に）
■ 私たちのイベントへの転用案（具体的なアクションで）
■ 診断士的ひとことメモ（環境分析・差別化の観点で一行）

私たちの文脈：
{OUR_CONTEXT}
"""
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}],
        tools=[{"type": "web_search_20250305", "name": "web_search"}],
    )
    # text ブロックだけ結合（tool_use/結果ブロックは除外）
    parts = [b.text for b in message.content if b.type == "text"]
    return "\n".join(p for p in parts if p).strip()


def build_report() -> str:
    sections = []
    for topic in RESEARCH_TOPICS:
        try:
            sections.append(research_topic(topic))
        except Exception as e:
            sections.append(f"【テーマ】{topic}\n（取得に失敗しました：{e}）")
    header = f"参考イベント 週次リサーチレポート（{date.today():%Y-%m-%d}）\n" + "=" * 30
    return header + "\n\n" + "\n\n---\n\n".join(sections)


def send_email(body: str):
    user = os.environ["GMAIL_USER"]
    app_pw = os.environ["GMAIL_APP_PASSWORD"]
    to = os.environ.get("MAIL_TO", user)

    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = Header(f"週次リサーチ {date.today():%m/%d}", "utf-8")
    msg["From"] = user
    msg["To"] = to

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(user, app_pw)
        server.send_message(msg)


if __name__ == "__main__":
    report = build_report()
    send_email(report)
    print("done")
