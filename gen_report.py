"""Generate the Lab1 Word report skeleton (text pre-filled, screenshot placeholders)."""
from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH

doc = Document()

# Base font
style = doc.styles["Normal"]
style.font.name = "Times New Roman"
style.font.size = Pt(11)


def h1(text):
    p = doc.add_heading(text, level=1)
    return p


def h2(text):
    p = doc.add_heading(text, level=2)
    return p


def para(text):
    p = doc.add_paragraph(text)
    return p


def screenshot(label):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run(f"【此处插入截图：{label}】")
    run.bold = True
    run.font.color.rgb = RGBColor(0xC0, 0x00, 0x00)


# ---------------- Cover ----------------
title = doc.add_paragraph()
title.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = title.add_run("杭州电子科技大学 网络安全实验报告")
r.bold = True
r.font.size = Pt(20)

doc.add_paragraph()
sub = doc.add_paragraph()
sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
sr = sub.add_run("Lab 1 — Secure REST API Development with CI/CD\nand Real CVE Vulnerability Analysis")
sr.bold = True
sr.font.size = Pt(14)

for _ in range(4):
    doc.add_paragraph()

for label in ["实验编号：Work 1", "变体号（Variant）：____________",
              "姓    名：____________", "学    号（HDU）：____________",
              "成    绩：____________"]:
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run(label)
    run.font.size = Pt(13)

doc.add_page_break()

# ---------------- 1. Objective ----------------
h1("一、实验目的")
para("1. 设计并实现一个符合安全规范的 RESTful 后端 API，覆盖 OWASP Top 10 中常见的"
     "身份认证、注入、跨站脚本等风险点。")
para("2. 在 CI/CD 流水线中集成 SAST（静态应用安全测试）与 SCA（软件成分分析），"
     "实现每次代码推送自动安全扫描。")
para("3. 基于 Vulhub/Docker 环境复现一个真实 CVE 漏洞，完成“漏洞复现 → 根因分析 → "
     "修复 → 验证”的完整安全开发生命周期。")

# ---------------- 2. Environment ----------------
h1("二、实验环境与技术栈")
table = doc.add_table(rows=6, cols=2)
table.style = "Light Grid Accent 1"
data = [
    ("操作系统", "Windows 11 / WSL2 (Docker Desktop)"),
    ("后端框架", "Python 3.11+ / Flask 3.0"),
    ("数据库", "SQLite 3（参数化查询）"),
    ("认证", "JWT (PyJWT, HS256, 30 min 过期)"),
    ("密码哈希", "bcrypt (cost factor = 12)"),
    ("CI/CD", "GitHub Actions：Bandit (SAST) + Safety (SCA)"),
]
for i, (k, v) in enumerate(data):
    table.rows[i].cells[0].text = k
    table.rows[i].cells[1].text = v

# ---------------- 3. API ----------------
h1("三、安全 REST API 实现")

h2("3.1 接口设计")
para("POST /auth/login —— 接收用户名与密码，校验成功后返回 JWT。")
para("GET  /api/data   —— 受保护接口，必须携带 Bearer JWT，返回当前用户创建的条目。")
para("POST /api/create —— 受保护接口（自定义接口），创建新条目，内容入库前做 HTML 转义。")

h2("3.2 安全措施")
para("（1）防 SQL 注入：所有 SQLite 查询均使用 ? 占位符绑定参数，例如 "
     "SELECT ... WHERE username = ?，全程不拼接 SQL 字符串。")
para("（2）防 XSS：用户输入经过 html.escape(quote=True) 转义后再入库；实测提交 "
     "<script>alert(1)</script> 后，数据库中存储为 &lt;script&gt;alert(1)&lt;/script&gt;。")
para("（3）身份认证：登录成功签发 HS256 JWT，有效期 30 分钟；受保护路由通过装饰器 "
     "@login_required 校验 JWT 签名与过期时间，缺失/非法 token 返回 401。")
para("（4）密码存储：使用 bcrypt（work factor 12）对密码加盐哈希，数据库仅存储哈希值，"
     "不存明文。对不存在的用户也执行一次 dummy bcrypt，缓解用户枚举时序攻击。")

h2("3.3 功能测试结果")
para("使用 curl 完成以下测试：")
para("  · GET /health 返回 200 {\"status\":\"ok\"}")
para("  · 不带 token 访问 /api/data 返回 401")
para("  · 错误密码登录返回 401")
para("  · 正确登录（alice / CorrectHorse9!）返回 JWT")
para("  · 带 token 访问 /api/data 返回 200，POST /api/create 返回 201，XSS payload 被转义")
screenshot("API 登录成功 + 401 拦截 + XSS 转义的 curl 输出")

# ---------------- 4. CI/CD ----------------
h1("四、CI/CD 安全流水线")
para("在 .github/workflows/ci.yml 中配置 GitHub Actions：每次 push 或 PR 到 main 自动执行。")
para("  · Bandit：对 app.py 做 SAST 静态扫描，检测危险函数、硬编码密钥、不安全调用。")
para("  · Safety：对 requirements.txt 做 SCA 成分分析，扫描第三方依赖已知 CVE。")
para("扫描报告以 artifact 形式上传。Actions 运行链接："
     "https://github.com/<你的用户名>/<你的仓库>/actions/runs/<run-id>")
screenshot("GitHub Actions 绿色成功标记 + Bandit/Safety 扫描结果")

# ---------------- 5. CVE repro ----------------
h1("五、CVE-2018-1000656 漏洞复现")

h2("5.1 漏洞描述")
table = doc.add_table(rows=5, cols=2)
table.style = "Light Grid Accent 1"
cve = [
    ("CVE 编号", "CVE-2018-1000656"),
    ("受影响产品", "Pallets Project Flask < 0.12.3"),
    ("修复版本", "Flask 0.12.3"),
    ("CWE", "CWE-20 输入校验不当"),
    ("影响", "未授权远程拒绝服务（内存暴涨）"),
]
for i, (k, v) in enumerate(cve):
    table.rows[i].cells[0].text = k
    table.rows[i].cells[1].text = v

h2("5.2 复现步骤")
para("（1）进入 vulhub-cve 目录，使用漏洞版 Dockerfile（pip install flask==0.12.2）启动靶场：")
para("    docker compose -f docker-compose.vuln.yml up --build -d")
para("（2）确认靶场正常：curl http://127.0.0.1:8000/")
para("（3）生成 5000 层嵌套的畸形 JSON：")
para("    python -c \"print('[' * 5000 + '1' + ']' * 5000)\" > payload.json")
para("（4）docker stats 记录攻击前内存基线。")
para("（5）发送攻击请求：")
para("    curl -H \"Content-Type: application/json\" --data-binary @payload.json http://127.0.0.1:8000/json")
para("（6）再次 docker stats，观察到容器内存暴涨、请求挂起或返回 500。")
screenshot("攻击前 docker stats 内存基线")
screenshot("攻击后 docker stats 内存暴涨（DoS 效果）")

h2("5.3 根因分析")
para("Flask 0.12.3 之前的 JSON 请求解析器在处理畸形或异常深层嵌套的 JSON 输入时，"
     "没有对解析代价/内存分配做边界限制。攻击者无需认证，只要向任何调用了 "
     "request.get_json() 的端点 POST 一个精心构造的 JSON body，就能让 Web 进程在返回错误前"
     "分配巨量内存，最终耗尽 Worker 甚至宿主机内存，造成拒绝服务。")

# ---------------- 6. Fix ----------------
h1("六、修复方案与验证")

h2("6.1 修复内容")
para("在 Dockerfile.fixed 中将 Flask 版本从 0.12.2 升级到 0.12.3：")
para("    RUN pip install --no-cache-dir flask==0.12.3")
para("0.12.3 对 JSON 解码器增加了输入边界校验，畸形/深嵌套 payload 会被快速拒绝（返回 400），"
     "不再导致内存膨胀。生产环境建议进一步升级到 Flask >= 2.3，并在容器上配置 mem_limit、"
     "反向代理限制请求体大小。")

h2("6.2 修复有效性验证")
para("关闭漏洞版，启动修复版后重放同一 PoC：")
para("    docker compose -f docker-compose.vuln.yml down")
para("    docker compose -f docker-compose.fixed.yml up --build -d")
para("    curl -i -H \"Content-Type: application/json\" --data-binary @payload.json http://127.0.0.1:8000/json")
para("预期：毫秒级返回 HTTP 400，docker stats 显示内存平稳，DoS 失效。")
screenshot("修复后 PoC 返回 HTTP 400 + 内存平稳")

h2("6.3 回归测试")
para("验证修复没有破坏正常业务：")
para("    curl -H \"Content-Type: application/json\" -d '{\"hello\":\"world\"}' http://127.0.0.1:8000/json")
para("预期返回：{\"echo\":{\"hello\":\"world\"}}，正常业务不受影响。")
screenshot("正常 JSON 回显接口仍正常工作（回归测试）")

# ---------------- 7. Questions ----------------
h1("七、控制思考题")
qa = [
    ("1. 为什么 bcrypt 比 SHA-256 更适合密码哈希？",
     "bcrypt 是自适应慢哈希，自带盐值，work factor 可调；SHA-256 是快速哈希且默认无盐，"
     "离线暴力破解和彩虹表攻击成本极低。"),
    ("2. SAST 与 DAST 的区别？",
     "SAST 在不运行程序的情况下审计源代码（白盒，如 Bandit）；DAST 对运行中的应用"
     "发起黑盒攻击（如 OWASP ZAP）。"),
    ("3. JWT 如何被服务器校验？",
     "服务器用相同的 secret 对 header+payload 重新签名，与请求中的签名比对，并校验 "
     "exp/iat 等时间声明。"),
    ("4. 不审计第三方依赖的风险？",
     "依赖库自身可能存在已知 CVE（如本次复现的 Flask 漏洞），SCA 能在代码合并前发现。"),
    ("5. Docker/Vulhub 相比本机直接装靶场的优势？",
     "环境隔离、版本精确锁定、可一键销毁复现，不污染宿主机。"),
    ("6. Vulnerability 与 Exploit 的区别？",
     "Vulnerability 是软件缺陷本身；Exploit 是触发该缺陷的具体代码/请求。本实验中 "
     "CVE-2018-1000656 是 vulnerability，嵌套 JSON 的 curl 请求是 exploit。"),
    ("7. 修复后为什么要做回归测试？",
     "确认补丁在堵住漏洞的同时没有破坏合法业务功能。"),
    ("8. 复现已知 CVE 对安全工程师的意义？",
     "建立对漏洞前置条件、利用方式、补丁行为的实操直觉，可直接迁移到 SOC 事件响应和渗透测试。"),
]
for q, a in qa:
    para(q)
    p = doc.add_paragraph(a)
    p.paragraph_format.left_indent = Cm(0.5)

# ---------------- 8. Summary ----------------
h1("八、实验总结")
para("通过本次实验，完整实践了安全 REST API 设计（参数化查询、输出转义、JWT 认证、"
     "bcrypt 密码哈希）、CI/CD 安全流水线（Bandit + Safety），并基于 Vulhub 复现并修复了 "
     "CVE-2018-1000656 Flask JSON 拒绝服务漏洞，理解了从漏洞复现到补丁验证的完整闭环。")

out = "Lab1-实验报告.docx"
doc.save(out)
print("saved:", out)
