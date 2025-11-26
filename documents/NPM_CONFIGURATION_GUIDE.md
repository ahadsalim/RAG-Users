,`/admin/*`, `/static/*`, `/media/*`, `/ws/*` اطلاعات هم

### Container Names (از docker-compose.yml):
- **Backend:** `app_backend` (port 8000)
- **Frontend:** `app_frontend` (port 3000)
- **NPM:** `app_npm`
- **Network:** `app_network`

### Domain:
- **Production:** `tejarat.chat`
- **Admin/API:** `admin.tejarat.chat` (فعلاً همه چیز به backend می‌ود)

---

## 📋 مر
2.اطلاعاتورودپش‌فرض (ولین بار):Email @xmpleom
   Pssword changeme   3پس زرو،رمز عورر غییردهیدFronttejarat.chatFrontendfront3SSL Tab:**
```
SSL ertificate: Reqea new SS Certifie (Let' Encrypt)
Force SSL ✓ (فعال)HTTP/2 Support: ✓ (فعال)HSTSEnabled: ✓ (فعال)
Email ressfr Let's Enryp: your-emal@example.cm
```

AdvancedTab:**

زرر CusmNgix Cfiguraion قرار دهید:
nginx# Frontd (Nxt.js)- Default
l {
    proxy_pss htt://app_frontend:3000;    proxy_set_adrHost $os;    prxy_set_heade X-Rel-IP $emote_adr;
   prxy_e_hedrX-Forwrded-For $roxy_add_xforwrd_for;    proxy_set_header X-de-ro$scheme;    prxy_redire ff;
    
  #Nxt.js WbSockt support
   prxy_htp_vers 1.1;
   proxy_set_her Upgrad$p_uge;
   prxy_eheCnne "upgrade";
}

#Next.jsl/_next {    proxy_passp://ap_frontend:3000;    expies 365d;
    add_hedeCache-Contrl "public, immutable";
}

# Next.j Image Optimizaio
loction /_next/iag {
    proxy_pass http:/front:3000;    prxy_set_hedeHs$host;}# Seurity Headers
add_header X-Frme-Ops"SAEORIGIN" always;
add_haer X-Content-Type-Optons"nosnff" away;add_hadrX-XSS-Prte "1;od=block" alwys;add_eader Refrrr-Policy"sric-origin-when-cross-igin" alays;
```

3. روی **Sve** کلیک کنید

---

### مرحله 3: تنظیم Poxy برای Backed (din.tjarat.chat)

#### 3.1 ایجاد roxy Host برایB
1. به **Hsts** → **Poxy Hosts** بروید
2. روی **Adrxy Hos** کلیککنیدDetlsTa:omain Nams: adm.tjarat.hCache Assets: ✗ (غیرفعال - برای API)
Block Common Exploits: ✓ (فعال)
 RequestanewSSLCertificate ()
Email Address for Let's Encrypt: your-email@example.comک زیرادر قرد for APIs;
    
    # CORS headers
    add_header Access-Control-Allow-Origin https://tejarat.chat always;
    add_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS, PATCH" always;
    add_header Access-Control-Allow-Headers "Authorization, Content-Type, X-Requested-With" always;
    add_header Access-Control-Allow-Credentials true always;
    
    # Handle preflight requests
    if ($request_method = 'OPTIONS') {
        add_header Access-Control-Allow-Origin https://tejarat.chat alway        add_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS, PATCH" always;
        add_header Access-Control-Allow-Headers "Authorization, Content-Type, X-Requested-With" always;
        add_header Access-Control-Max-Age 1728000;
        add_header Content-Type 'text/plain charset=UTF-8';
        add_header Content-Length 0;
        return 204;
    }
# Django Admin Pane
l# Static Fies (Djang)
loaliic
# Media Files (User uploads)alimi
# WebSocket ConnectionScrHmOtins "SAMEORIGIN" lys;
aCnnt-Tp-Opin"nonf"alwaX-XSS-Prt1mod=bk"lwyReferrrPy"str-rin-whn-c-rigi"alwa3🔧ضاف(خت)فزونwwwubo
اگر می‌خواهید `www` هم کار کند

1 Proxy Hos مربوط به `t را ویرایش کنید2.در**DmaiName**ضفهی         www   بایجلوگیری از bus،می‌توانید rte limiting اضافه کنیددر بالای فایل Advncdcofiاضافهکنید:# در اضافهکنید:

برایlginedpont:proxy_pass http://app_backend:8000;
    ---

🧪 تست تنظیمت

پس ا ذخیره، ایURLها را تست کنید:

### ✅ Fonn URL (باید کار کنند):bashl-I https://tjt.ct/
culI https://teja.chat/auth/lgi
curl-https://tejrt.cht/asbor
```

### ✅Backd URL (بایدکارکنند):
```bhcurl -I https://min.tja.ha/ap/v/auth/gin/
url -Ihttp://min.tja.ha/adm/
ul Ihttp://.tjarat.hat/stc/ad/ss/bs.cs52 BadGatewayoner درسست
```bash#بررسیضعت containers
docker ps | grep-E"app_bakend|pp_fronend|app_pm"

#بسnetwork
doker newrkinspet pp_newrk

# بررسیلاگ‌هdocker logs app_backend--tail50
dockerlogs--ail 50
dcke logsapp_npm--tail50
```4 GatewayTimeoutTimoutکواهادAdvn cnfig،timoutهاا افزاشدید:
```nginxprxy_onnt_timeut 300s;
rxy_end_timout300s;
prxy_red_timout 300s;
```## مشکل 3: CORSErrors

**عل:** CORS headers درنظیم نشده

**ره ح:**
مطمئنشویدکدر lto`/i کد CORS را اضافه کرده‌اید (در بالا آمده است)4tati/MdiaFilesVolume هmunنشده‌دdocke-cmpe.ymlNPMvlumبررسی:```yaml
volumes:
- ati_files:/stc:r
-meia_fils:/media:ro```
 داخل NPMdtasdfault-hst_accessdtasdfault-hot_errorبرریNetwokلیotainersدر networkdokenework sp p_newrk | rep -A 5 "Contaers"اتصال از NPM به backdokeexecpp_np pg -c 3 pp_bkendاصلزNPMبه frond
docke exe pp_np png  3 pp_frtendهمه containers در network `app_network` هستند
- [ ] `tejrat.chat`SSL erifie.ejra.htفعالاسFrontnd (`tejra.h)`app_:3000`proxyشوBaked (`dm.tjaat.chat`)به`app_backend:8000` proxy م‌شود
-[ ] CORS hadesبرای API ظیم شهStaticوMiails دردسرسهندتسURLهfrontnd و bckdوفقتآمیز است🔐مت### توصیه‌هیان**تغیر رمز عبور:** حتماًمزپیش‌فض ا تغیرده **محدود کردندسرس بهpt 81:** فقطزIPمشخص**فعالکرنFl2Ba:**بایجوگیریز brute force
4. **بروزسنیمظم:** NPM و SSL certificates5**Bkup:** ازتنظیاتNPMbackupبگیرContainerNmes:نام‌ها دقق containerاسفاده کد (`app_backend`,`app_frontend`)Network:همcontainersید`ap_newrk` باشند**Ports: ز port یدخلیسفاده (8000,3000)هexternalL:** et's Encryptایگان است، حتمً
5. **CORS: APIضروراس6Stic Fils:** ازvoueهی shared ستادم‌شو

---

## 🆘پشتیانی

اگ مشکلی دشتد:

1.ا‌ها NPM را برسی کنید
2. تنظمات networkر چک کنید
3. مطمئن شوید همهcontiner در حال اجرا هستند
4. Cache مرورگر را پاک کنید
5. DNS را بررسی کنید (A rcord ها)  2 (اصلاح شده با توجه به docker-compose.yml)