# CORTEX-GUARD MVP v1

إضافة Chrome تجريبية لتحليل الصفحة الحالية بحثًا عن مؤشرات تصيّد ثابتة. تجمع الإضافة عنوان الصفحة والنص الظاهر فقط، وترسل طلب التحليل إلى backend محلي.

## الحالة

هذا إصدار مسابقة تجريبي بقواعد deterministic ومطابقة نصية مباشرة. نتيجة الديمو تثبت مسار العمل، ولا تمثل قياسًا لدقة الكشف على مواقع العالم الحقيقي. لا يوجد نموذج تعلم آلي أو تكامل سحابي.

## الوظائف

- تحليل يدوي للصفحة الحالية عند الضغط على زر الإضافة.
- إرسال URL والنص الظاهر إلى `http://localhost:8000`.
- استخراج مؤشرات urgency وOTP والتهديدات وكلمات URL المحددة.
- تتبع تسلسل الأحداث داخل ذاكرة backend لكل جلسة مرتبطة بتبويب.
- إظهار درجة الخطر على badge، وإشعار Chrome بالأدلة عند `risk_score >= 0.6`.

## المتطلبات

- Python 3.12
- Chrome يدعم Manifest V3

## تشغيل Backend على Windows

من مجلد المشروع:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m uvicorn backend.app.main:app --host localhost --port 8000
```

يبقى الخادم محليًا على `http://localhost:8000`. أوقفه بـ `Ctrl+C`.

## تحميل الإضافة محليًا

1. افتح `chrome://extensions`.
2. فعّل Developer mode.
3. اختر Load unpacked وحدد مجلد `extension/`.
4. ثبّت CORTEX-GUARD في شريط الأدوات من قائمة الإضافات إذا لم تظهر أيقونته، ثم افتح صفحة ويب واضغط الأيقونة لتحليلها.

لتجربة السياق متعدد الخطوات، حلّل بالتتابع صفحة رسالة استعجال، ثم صفحة رابط مشبوه، ثم صفحة تطلب رمز تحقق وتحتوي أيضًا إشارات استعجال وتهديد وكلمات URL مشبوهة، مع البقاء في التبويب نفسه. درجة الخطر تجمع خصائص الصفحة الحالية ولا تجمعها رقميًا من الصفحات السابقة.

### صفحات الديمو المحلية

بعد تشغيل backend وتحميل الإضافة في Chrome، افتح نافذة PowerShell ثانية من مجلد المشروع وشغّل:

```powershell
python -m http.server 8001 --bind localhost --directory demo/pages
```

في Chrome، افتح `http://localhost:8001/01-message.html` واضغط أيقونة CORTEX-GUARD. انتقل في التبويب نفسه إلى `http://localhost:8001/02-link.html` ثم `http://localhost:8001/03-otp.html`، واضغط الأيقونة بعد كل انتقال. النتيجة الأخيرة المتوقعة: badge يعرض `0.62`، والوسم `phishing`، والسياق `multi_step_attack`، وإشعار بالأدلة. أسماء النطاقات في الصفحات أمثلة محجوزة ولا تحتاج اتصالًا بها.

أوقف خادم الصفحات وخادم backend بـ `Ctrl+C` بعد التجربة.

## الاختبارات والديمو

```powershell
python -m pytest backend/app/tests -q
python backend/app/tests/demo_scenario.py
```

السيناريو المتوقع يطبع `multi_step_attack` مع درجة خطر تتجاوز `0.6` وسلسلة الأدلة. يحتاج تشغيل الاختبارات إلى تثبيت المتطلبات أولًا.

## API

### `POST /analyze`

```json
{
  "type": "text",
  "content": "http://verify.example.test urgent verification code required for login account suspend blocked",
  "session_id": "tab-session-id",
  "event_type": "otp_request"
}
```

قيم `type`: `text`, `url`, `file`. قيم `event_type`: `message`, `link`, `otp_request`, `file`.

بعد تسلسل الديمو في الجلسة نفسها، تكون استجابة الحدث الأخير:

```json
{
  "risk_score": 0.6166666666666667,
  "label": "phishing",
  "context_pattern": "multi_step_attack",
  "evidence_chain": [
    "Urgency language detected",
    "Suspicious URL detected",
    "OTP request detected",
    "Multi-step attack pattern matched"
  ]
}
```

### `GET /session/{session_id}`

يعيد أحداث الجلسة الموجودة في ذاكرة backend الحالية. تُحذف الجلسات عند توقف العملية.

## الخصوصية والنطاق

- البيانات المرسلة: عنوان الصفحة والنص الظاهر فقط.
- لا يستخدم المشروع سجل التصفح أو كلمات المرور أو ضغطات المفاتيح أو بيانات النماذج.
- لا تُرسل البيانات إلى خدمة سحابية ولا تحفظ في قاعدة بيانات.
- لا توجد مراقبة مستمرة؛ التحليل يبدأ يدويًا.
- الملفات المحلية خارج النطاق. فحص امتداد `.txt` أو `.pdf` لا يعني قراءة ملفات الجهاز.

## حدود معروفة

- قواعد الكشف قائمة على كلمات إنجليزية ثابتة ولم تُعاير على مجموعة اختبار واقعية؛ لا تستخدم النتيجة كتأكيد أمني نهائي.
- خصائص المخاطر تُحسب من مدخل التحليل الحالي، ولا تُجمع رقميًا عبر أحداث الجلسة؛ السياق يكتشف التسلسل فقط. صفحة تحتوي طلب OTP وحده قد تنتج خطرًا منخفضًا.
- وزن `file_risk` الحالي `0.1` كقيمة تنفيذية مؤقتة؛ مواصفة الأوزان لا تحدد وزنًا للملف.
- شرط زيادة وزن السياق عند `context_risk > 0.7` لا يتحقق مع قيمة النمط الحالية `0.6`.
- الإضافة تعرض الرقم والأدلة عبر badge وإشعار Chrome، ولا توفر لوحة أو نافذة نتائج.
- يلزم اختبار الإضافة يدويًا في Chrome على جهاز العرض قبل المسابقة.

## بنية المشروع

```text
LICENSE                 ترخيص MIT
backend/app/core/       الثوابت والإعدادات
backend/app/schemas/    عقود البيانات
backend/app/services/   مراحل التحليل المنفصلة
backend/app/routes/     نقاط API
backend/app/tests/      اختبارات الوحدات والسيناريو التجريبي
demo/pages/             صفحات محلية ثابتة لتجربة سيناريو المسابقة
extension/              Manifest V3 وcontent/background scripts
docs/                   توثيق المشروع وتقارير الجاهزية
```

## التعديل بمساعدة الذكاء الاصطناعي

اقرأ [`AGENTS.md`](AGENTS.md) قبل طلب أي تعديل برمجي؛ يحتوي حدود الخصوصية والمعمارية والاختبارات المطلوبة للمساهمات.

## الترخيص

هذا المشروع مرخص وفق MIT. راجع ملف [`LICENSE`](LICENSE) لمعرفة شروط الاستخدام وإعادة التوزيع.
