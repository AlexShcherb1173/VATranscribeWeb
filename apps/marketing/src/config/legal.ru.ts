import type { LegalDocumentConfig } from "./legal";
import { LEGAL_EFFECTIVE_DATE, LEGAL_VERSION } from "./legal";

export const legalDocumentsRu: LegalDocumentConfig[] = [
  {
    "documentType": "terms",
    "slug": "terms",
    "path": "/ru/legal/terms",
    "title": "Условия использования",
    "shortTitle": "Условия",
    "requiredForRegistration": true,
    "summary": "Условия доступа к VATranscribe: аккаунт, обработка медиа, квоты, допустимое использование и ограничения сервиса.",
    "notice": "VATranscribe работает в pre-release режиме от имени физлица / самозанятого. Платные списания отключены до подключения проверенного платёжного процесса.",
    "sections": [
      {
        "title": "1. Область действия",
        "paragraphs": [
          "Настоящие Условия регулируют доступ к VATranscribe, включая публичный сайт, личный кабинет, API-backed upload, download, transcription, export, quota и account functionality.",
          "Создавая аккаунт или используя защищённые функции, пользователь принимает настоящие Условия и обязательные юридические документы, показанные при регистрации."
        ]
      },
      {
        "title": "2. Оператор и контакты",
        "paragraphs": [
          "Тип оператора: физлицо / самозанятый.",
          "ФИО, адрес и регистрационные данные оператора задаются через production-настройки LEGAL_* и должны быть финализированы до публичного production-запуска.",
          "Юридический контакт: legal@vatranscribe.ru. Поддержка: support@vatranscribe.ru."
        ]
      },
      {
        "title": "3. Аккаунт и безопасность",
        "paragraphs": [
          "Пользователь отвечает за сохранность учётных данных и действия, выполненные через его аккаунт."
        ],
        "bullets": [
          "Сервис может применять password policy, refresh token rotation, CSRF protection и rate limits.",
          "Сервис может завершать сессии или ограничивать аккаунты, создающие security или abuse риск."
        ]
      },
      {
        "title": "4. Обработка медиа",
        "paragraphs": [
          "Пользователь отвечает за наличие прав и разрешений на загрузку, скачивание, обработку, транскрибацию, хранение и экспорт переданных материалов.",
          "Сервис нельзя использовать для незаконного контента, нарушения прав, abusive automation, попыток несанкционированного доступа или обхода ограничений третьих платформ."
        ]
      },
      {
        "title": "5. YouTube cookies",
        "paragraphs": [
          "Если функция включена, пользователь может загрузить Netscape cookies.txt для собственных задач. Файл хранится зашифрованным и изолированным по пользователю, используется только для задач пользователя и может быть удалён или заменён пользователем.",
          "Пользователь самостоятельно отвечает за соблюдение правил сторонних платформ."
        ]
      },
      {
        "title": "6. Квоты и лимиты",
        "paragraphs": [
          "VATranscribe может применять лимиты на storage, upload, download, export, transcription, jobs и rate limits. Операции могут быть отклонены, остановлены или очищены по retention policy."
        ]
      },
      {
        "title": "7. Биллинг",
        "paragraphs": [
          "Платный биллинг и активация платных тарифов отключены до подключения production payment provider и verified payment workflow."
        ]
      },
      {
        "title": "8. Privacy requests и удаление",
        "paragraphs": [
          "Пользователь может запросить экспорт, удаление или исправление данных, где это юридически и технически применимо. Часть записей может сохраняться для security, legal, billing или audit purposes."
        ]
      }
    ],
    "version": LEGAL_VERSION,
    "effectiveDate": LEGAL_EFFECTIVE_DATE
  },
  {
    "documentType": "privacy",
    "slug": "privacy",
    "path": "/ru/legal/privacy",
    "title": "Политика конфиденциальности",
    "shortTitle": "Конфиденциальность",
    "requiredForRegistration": true,
    "summary": "Политика описывает категории данных, цели обработки, сроки хранения, права пользователя и статус сторонних процессоров VATranscribe.",
    "notice": "Для P2-01 сторонние процессоры считаются disabled, если они явно не включены в production legal settings.",
    "sections": [
      {
        "title": "1. Оператор",
        "paragraphs": [
          "VATranscribe работает от имени физлица / самозанятого в pre-release режиме. Данные оператора задаются через LEGAL_* настройки и должны быть финализированы до публичного production-запуска.",
          "Privacy contact: privacy@vatranscribe.ru. Legal contact: legal@vatranscribe.ru."
        ]
      },
      {
        "title": "2. Категории данных",
        "bullets": [
          "Account: email, password hash, account status, profile/display name при наличии.",
          "Security: IP address, user-agent, audit logs, refresh token hashes, CSRF cookie metadata и security events.",
          "Files: uploaded audio/video, downloaded media, generated transcripts, export artifacts txt/srt/vtt/json и job metadata.",
          "YouTube cookies: зашифрованный per-user Netscape cookies.txt, если пользователь его загрузил.",
          "Billing: plan, subscription status, payment status, provider transaction id, invoices/receipts при включении платежей.",
          "Monitoring: Sentry events, error traces и technical logs при включении мониторинга."
        ]
      },
      {
        "title": "3. Цели обработки",
        "bullets": [
          "Регистрация и вход пользователя.",
          "Предоставление upload, download, transcription и export workflows.",
          "Хранение результатов в личном кабинете.",
          "Защита аккаунтов и сессий.",
          "Audit logging и abuse prevention.",
          "Quota, usage и subscription accounting.",
          "Поддержка и privacy request handling.",
          "Выполнение юридических обязанностей и поддержание надёжности сервиса.",
          "Analytics и улучшение сервиса только после согласия, если analytics включена."
        ]
      },
      {
        "title": "4. Сроки хранения",
        "bullets": [
          "Uploaded/downloaded media: 30 days by default or until user deletion.",
          "Export artifacts: 14 days by default or until user deletion.",
          "Transcripts: 90 days by default or until user deletion.",
          "Temporary files: 24 hours.",
          "Failed job files: 7 days.",
          "Audit/security logs: 180 days.",
          "Account deletion processing window: 30 days.",
          "Backups: 7 daily, 4 weekly, 6 monthly.",
          "Billing records: disabled until billing is enabled or retained as required by law."
        ]
      },
      {
        "title": "5. Третьи стороны",
        "paragraphs": [
          "Для P2-01 hosting, CDN, analytics, APM, payment и email processors считаются disabled, если не настроены отдельно. При включении нужно указать реальные названия провайдеров, страны и детали передачи данных."
        ]
      },
      {
        "title": "6. Права пользователя",
        "bullets": [
          "Запросить доступ к персональным данным.",
          "Запросить экспорт данных, где поддерживается.",
          "Запросить удаление, где это юридически и технически возможно.",
          "Запросить исправление неточных данных.",
          "Отозвать согласие, если обработка основана на согласии."
        ]
      },
      {
        "title": "7. Статус 152-ФЗ",
        "paragraphs": [
          "Если сервис обрабатывает персональные данные граждан РФ, до публичного production-запуска нужно закрыть готовность по 152-ФЗ: статус оператора, решение по локализации и статус уведомления Роскомнадзора, где применимо."
        ]
      }
    ],
    "version": LEGAL_VERSION,
    "effectiveDate": LEGAL_EFFECTIVE_DATE
  },
  {
    "documentType": "personal_data",
    "slug": "personal-data",
    "path": "/ru/legal/personal-data",
    "title": "Согласие на обработку персональных данных",
    "shortTitle": "Персональные данные",
    "requiredForRegistration": true,
    "summary": "Согласие на обработку данных, необходимых для аккаунта, аутентификации, media workflows, audit logs, quota accounting и privacy requests.",
    "notice": "Согласие отделено от Условий и Политики конфиденциальности и обязательно при регистрации.",
    "sections": [
      {
        "title": "1. Область согласия",
        "paragraphs": [
          "Принимая этот документ, пользователь даёт согласие на обработку персональных данных, необходимых для работы VATranscribe."
        ]
      },
      {
        "title": "2. Состав данных",
        "bullets": [
          "Account и authentication data.",
          "Security logs и audit events.",
          "Uploaded/downloaded media, transcripts и export artifacts.",
          "YouTube cookies.txt, если пользователь его загружает.",
          "Quota, usage, subscription и billing-related data при включении платежей.",
          "Support и privacy request data."
        ]
      },
      {
        "title": "3. Операции обработки",
        "paragraphs": [
          "Обработка может включать сбор, запись, систематизацию, хранение, уточнение, извлечение, использование, передачу настроенным процессорам при необходимости, блокирование, удаление и уничтожение."
        ]
      },
      {
        "title": "4. Отзыв согласия",
        "paragraphs": [
          "Пользователь может отозвать согласие, если обработка основана на согласии. Отзыв может ограничить доступ к сервису. Некоторые записи могут продолжать обрабатываться для безопасности, юридических обязанностей, биллинга, разрешения споров или audit evidence."
        ]
      }
    ],
    "version": LEGAL_VERSION,
    "effectiveDate": LEGAL_EFFECTIVE_DATE
  },
  {
    "documentType": "cookies",
    "slug": "cookies",
    "path": "/ru/legal/cookies",
    "title": "Политика cookies",
    "shortTitle": "Cookies",
    "requiredForRegistration": false,
    "summary": "Политика описывает essential cookies, browser storage и модель analytics/marketing tracking, отключённую по умолчанию.",
    "notice": "Analytics и marketing cookies отключены для P2-01, если они не включены отдельной consent-aware интеграцией.",
    "sections": [
      {
        "title": "1. Essential cookies",
        "paragraphs": [
          "VATranscribe может использовать cookies и browser storage, необходимые для authentication, CSRF protection, session security, language и interface preferences."
        ]
      },
      {
        "title": "2. Non-essential tracking",
        "paragraphs": [
          "Analytics cookies, marketing pixels и CRM/ad pixels отключены, если не настроены явно и не привязаны к согласию там, где это требуется."
        ]
      },
      {
        "title": "3. Выбор пользователя",
        "paragraphs": [
          "При включении non-essential tracking пользователь должен получить понятный выбор до активации таких технологий, если это требуется законом."
        ]
      }
    ],
    "version": LEGAL_VERSION,
    "effectiveDate": LEGAL_EFFECTIVE_DATE
  },
  {
    "documentType": "refund",
    "slug": "refund",
    "path": "/ru/legal/refund",
    "title": "Политика возвратов",
    "shortTitle": "Возвраты",
    "requiredForRegistration": false,
    "summary": "Политика возвратов для текущего состояния, где платный биллинг отключён до подключения проверенного payment provider.",
    "notice": "Платные подписки нельзя включать до финализации payment provider, refund rules, invoices и fiscal receipt requirements.",
    "sections": [
      {
        "title": "1. Текущий статус биллинга",
        "paragraphs": [
          "Платный биллинг отключён для P2-01. Сервис может показывать планы и квоты, но активация платного тарифа требует production payment provider и verified webhook flow."
        ]
      },
      {
        "title": "2. Будущие платежи",
        "paragraphs": [
          "До включения платежей сервис должен опубликовать точные цены, billing period, renewal, cancellation, refund, invoice и fiscal receipt rules."
        ]
      },
      {
        "title": "3. Контакт",
        "paragraphs": [
          "Вопросы по биллингу и возвратам направляются на настроенный support contact."
        ]
      }
    ],
    "version": LEGAL_VERSION,
    "effectiveDate": LEGAL_EFFECTIVE_DATE
  }
];

export function getLegalDocumentRuBySlug(slug: string): LegalDocumentConfig | undefined {
  return legalDocumentsRu.find((document) => document.slug === slug);
}
