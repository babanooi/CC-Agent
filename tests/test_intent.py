
import sys, os, json

os.environ['SSL_CERT_FILE'] = r'D:\\py_study\\py_study2\\RAG + FastAPI\\.venv\\Lib\\site-packages\\certifi\\cacert.pem'
os.environ['REQUESTS_CA_BUNDLE'] = r'D:\\py_study\\py_study2\\RAG + FastAPI\\.venv\\Lib\\site-packages\\certifi\\cacert.pem'

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import dashscope
from config import config_data as config

dashscope.api_key = config.dashscope_api_key

INTENTS = {
    "product_query": "询问产品参数功能规格",
    "product_compare": "对比两款产品差异",
    "troubleshoot": "手机故障需要排查",
    "purchase_advice": "想要购买建议推荐",
    "chitchat": "闲聊打招呼告别",
}

def classify(message):
    intent_desc = "\n".join(f"- {k}: {v}" for k, v in INTENTS.items())
    prompt = f"将用户消息分类：\n{intent_desc}\n\nJSON格式输出：{{\"intent\":\"类别名\",\"confidence\":0.95,\"reason\":\"原因\"}}\n只输出JSON。\n\n用户消息：{message}"
    
    from dashscope import Generation
    resp = Generation.call(model="qwen-turbo", prompt=prompt, api_key=config.dashscope_api_key, result_format="message")
    content = resp.output.choices[0].message.content
    
    import re
    try:
        return json.loads(content)
    except:
        m = re.search(r'\{[^}]+\}', content)
        return json.loads(m.group()) if m else {"intent": "unknown"}

if __name__ == "__main__":
    print("意图分类器测试")
    print("=" * 50)
    
    tests = [
        ("你好呀", "chitchat"),
        ("小米15 Pro电池多大？", "product_query"),
        ("小米15 Pro和华为Mate 70 Pro哪个好？", "product_compare"),
        ("我手机充不进电了怎么办", "troubleshoot"),
        ("5000块推荐个手机", "purchase_advice"),
    ]
    
    correct = 0
    for q, expected in tests:
        r = classify(q)
        actual = r.get("intent", "?")
        ok = actual == expected
        if ok: correct += 1
        conf = r.get("confidence", 0)
        print(f"{'✅' if ok else '❌'} [{actual}] conf={conf:.2f} | {q}")
        if not ok:
            print(f"   预期: {expected}")
    
    print(f"\n准确率: {correct}/{len(tests)} ({correct/len(tests)*100:.0f}%)")
