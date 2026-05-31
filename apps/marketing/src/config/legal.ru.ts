import type { LegalDocumentConfig } from "./legal";
import { LEGAL_EFFECTIVE_DATE, LEGAL_VERSION } from "./legal";

export const legalDocumentsRu: LegalDocumentConfig[] = [
  {
    documentType: "terms",
    slug: "terms",
    path: "/ru/legal/terms",
    title: "Условия использования",
    shortTitle: "Условия",
    version: LEGAL_VERSION,
    effectiveDate: LEGAL_EFFECTIVE_DATE,
    requiredForRegistration: true,
    summary:
      "Условия доступа к VATranscribe: аккаунт, обработка медиа, подписки, допустимое использование и ограничения сервиса.",
    notice:
      "Это структурированный черновик. Перед production необходимо заменить данные компании, юрисдикцию и коммерческие условия.",
    sections: [
      {
        title: "1. Область действия",
        paragraphs: [
          "Настоящие Условия регулируют доступ к VATranscribe, включая публичный сайт, web dashboard, API-backed media workflows, скачивание, транскрибацию и связанные сервисы.",
          "Создавая аккаунт или используя сервис, пользователь принимает эти Условия и юридические документы, указанные при регистрации."
        ]
      },
      {
        title: "2. Аккаунт",
        paragraphs: [
          "Для доступа к защищённым функциям может потребоваться аккаунт.",
          "Пользователь отвечает за безопасность учётных данных и действия, выполненные через его аккаунт."
        ],
        bullets: [
          "Backend может отклонять слабые пароли.",
          "Сервис может использовать access tokens и refresh token rotation.",
          "Сессия может быть завершена при нарушении security-политик."
        ]
      },
      {
        title: "3. Обработка медиа",
        paragraphs: [
          "VATranscribe может обрабатывать ссылки, загруженные файлы, media assets, транскрипты и export artifacts.",
          "Пользователь отвечает за наличие прав на скачивание, обработку, хранение и экспорт переданных материалов."
        ],
        bullets: [
          "Нельзя обрабатывать контент, нарушающий права третьих лиц.",
          "Нельзя использовать сервис для незаконной или вредоносной активности.",
          "Нельзя обходить ограничения, лимиты и security controls."
        ]
      },
      {
        title: "4. Тарифы и лимиты",
        paragraphs: [
          "VATranscribe может предоставлять бесплатные и платные планы с разными лимитами и возможностями.",
          "Лимиты могут применяться к storage, transcription seconds, количеству задач, скачиванию и экспорту."
        ]
      },
      {
        title: "5. Доступность сервиса",
        paragraphs: [
          "Функции сервиса могут изменяться, приостанавливаться или отключаться в процессе разработки.",
          "Production SLA требует отдельного письменного соглашения."
        ]
      },
      {
        title: "6. Прекращение доступа",
        paragraphs: [
          "Сервис может ограничить или прекратить доступ при нарушении условий, злоупотреблении инфраструктурой или security-рисках.",
          "Пользователь может запросить экспорт или удаление данных через privacy request workflow, если такая функция доступна."
        ]
      }
    ]
  },
  {
    documentType: "privacy",
    slug: "privacy",
    path: "/ru/legal/privacy",
    title: "Политика конфиденциальности",
    shortTitle: "Конфиденциальность",
    version: LEGAL_VERSION,
    effectiveDate: LEGAL_EFFECTIVE_DATE,
    requiredForRegistration: true,
    summary:
      "Политика описывает, какие данные может обрабатывать VATranscribe, зачем они используются, как хранятся и как пользователь может запросить доступ или удаление.",
    notice:
      "Это структурированный черновик. Перед запуском нужно уточнить юрисдикцию, оператора, процессоров, аналитику и сроки хранения.",
    sections: [
      {
        title: "1. Оператор данных",
        paragraphs: [
          "Перед production необходимо указать юридическое лицо или оператора сервиса, адрес и контактный email.",
          "Политика применяется к маркетинговому сайту, web dashboard, API и связанным media workflows."
        ]
      },
      {
        title: "2. Какие данные могут обрабатываться",
        bullets: [
          "Аккаунт: email, password hash, статус аккаунта и даты.",
          "Security data: события аутентификации, refresh tokens, IP-derived metadata и audit logs.",
          "Usage data: задачи, квоты, metadata media assets, transcripts и exports.",
          "User-submitted data: ссылки, загруженные файлы, транскрипты и комментарии в privacy requests.",
          "Billing data: план, статус подписки, usage history и provider references при включении оплат."
        ]
      },
      {
        title: "3. Цели обработки",
        bullets: [
          "Создание и управление аккаунтом.",
          "Аутентификация и защита сессий.",
          "Обработка download и transcription jobs.",
          "Применение квот, подписок и лимитов.",
          "Хранение версий согласий.",
          "Обработка privacy requests."
        ]
      },
      {
        title: "4. Сроки хранения",
        paragraphs: [
          "Данные аккаунта, media, transcripts, audit и billing records могут храниться пока аккаунт активен или пока это требуется для безопасности, биллинга, разрешения споров и юридических обязанностей.",
          "Точные retention periods должны быть финализированы перед production."
        ]
      },
      {
        title: "5. Права пользователя",
        bullets: [
          "Запросить доступ к персональным данным.",
          "Запросить экспорт данных.",
          "Запросить удаление данных, где это применимо.",
          "Запросить исправление неточных данных.",
          "Отозвать согласие, если обработка основана на согласии."
        ]
      }
    ]
  },
  {
    documentType: "personal_data",
    slug: "personal-data",
    path: "/ru/legal/personal-data",
    title: "Согласие на обработку персональных данных",
    shortTitle: "Персональные данные",
    version: LEGAL_VERSION,
    effectiveDate: LEGAL_EFFECTIVE_DATE,
    requiredForRegistration: true,
    summary:
      "Согласие на обработку персональных данных, необходимых для аккаунта, аутентификации, media workflows, audit logs и privacy requests.",
    notice:
      "Это черновик согласия. Перед production текст нужно адаптировать под фактическую юрисдикцию и бизнес-структуру.",
    sections: [
      {
        title: "1. Область согласия",
        paragraphs: [
          "Принимая этот документ при регистрации, пользователь соглашается на обработку данных, необходимых для работы VATranscribe.",
          "Это может включать данные аккаунта, authentication data, consent records, privacy request data, metadata media workflows и billing-related data."
        ]
      },
      {
        title: "2. Цели обработки",
        bullets: [
          "Создание аккаунта и аутентификация.",
          "Защита сессий и refresh token rotation.",
          "Работа download, upload, transcription и export workflows.",
          "Управление квотами и подписками.",
          "Хранение версий юридических согласий.",
          "Security audit logging."
        ]
      },
      {
        title: "3. Отзыв согласия",
        paragraphs: [
          "Пользователь может запросить отзыв согласия, если это применимо.",
          "Некоторые записи могут сохраняться при наличии юридических, security, billing или audit-оснований."
        ]
      }
    ]
  },
  {
    documentType: "cookies",
    slug: "cookies",
    path: "/ru/legal/cookies",
    title: "Политика cookies",
    shortTitle: "Cookies",
    version: LEGAL_VERSION,
    effectiveDate: LEGAL_EFFECTIVE_DATE,
    requiredForRegistration: false,
    summary:
      "Политика cookies описывает essential cookies, local storage, analytics cookies и будущие настройки tracking technologies.",
    notice:
      "Перед production нужно добавить фактический список cookies и analytics-инструментов.",
    sections: [
      {
        title: "1. Что такое cookies",
        paragraphs: [
          "Cookies и похожие технологии помогают сайту сохранять состояние, защищать сессии, измерять использование и улучшать UX.",
          "VATranscribe также может использовать browser storage для authentication state, темы, языка и настроек интерфейса."
        ]
      },
      {
        title: "2. Essential technologies",
        bullets: [
          "Хранение, необходимое для входа в аккаунт.",
          "Security storage для защиты доступа.",
          "Preference storage для темы, языка и UI-настроек."
        ]
      },
      {
        title: "3. Analytics и marketing",
        paragraphs: [
          "Analytics-инструменты не финализированы. Если будут добавлены Google Analytics, Яндекс Метрика, PostHog или другие сервисы, их нужно перечислить здесь.",
          "Где это требуется законом, non-essential cookies должны включаться только после согласия пользователя."
        ]
      }
    ]
  },
  {
    documentType: "refund",
    slug: "refund",
    path: "/ru/legal/refund",
    title: "Политика возвратов",
    shortTitle: "Возвраты",
    version: LEGAL_VERSION,
    effectiveDate: LEGAL_EFFECTIVE_DATE,
    requiredForRegistration: false,
    summary:
      "Черновик политики возвратов для будущих подписок, смены тарифов, ошибок платежей, trial-периодов и исключительных возвратов.",
    notice:
      "Коммерческие правила возвратов нужно финализировать до включения платных подписок.",
    sections: [
      {
        title: "1. Текущий статус",
        paragraphs: [
          "VATranscribe подготовлен к будущему SaaS billing и subscription functionality.",
          "Платные условия должны быть финализированы до production-платежей."
        ]
      },
      {
        title: "2. Подписки",
        paragraphs: [
          "Платные планы могут оплачиваться ежемесячно или ежегодно.",
          "До оплаты пользователь должен видеть тариф, период, лимиты, renew/cancel поведение."
        ]
      },
      {
        title: "3. Возвраты",
        paragraphs: [
          "Production-политика может предусматривать возвраты при двойном списании, технической ошибке платежа или если это требуется законом.",
          "Если выбран no-refund подход для использованных digital services, его нужно явно раскрыть до оплаты."
        ]
      }
    ]
  }
];

export function getLegalDocumentRuBySlug(slug: string): LegalDocumentConfig | undefined {
  return legalDocumentsRu.find((document) => document.slug === slug);
}