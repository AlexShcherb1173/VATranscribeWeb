import { useEffect, useState } from "react";

import { env } from "@/shared/config/env";
import { getCookieConsent, saveCookieConsent, type CookieConsentState } from "@/shared/cookies/consent";

type DraftConsent = {
  analytics: boolean;
  marketing: boolean;
};

export function CookieConsentBanner() {
  const [visible, setVisible] = useState(false);
  const [draft, setDraft] = useState<DraftConsent>({ analytics: false, marketing: false });

  useEffect(() => {
    if (!env.cookieConsentRequired) {
      return;
    }

    const current = getCookieConsent();
    if (!current) {
      setVisible(true);
      return;
    }

    setDraft({ analytics: current.analytics, marketing: current.marketing });
  }, []);

  function persist(consent: DraftConsent): CookieConsentState {
    const saved = saveCookieConsent(consent);
    setDraft({ analytics: saved.analytics, marketing: saved.marketing });
    setVisible(false);
    return saved;
  }

  if (!visible) {
    return null;
  }

  return (
    <section className="cookie-consent" aria-label="Cookie consent">
      <div className="cookie-consent__content">
        <strong>Cookie preferences</strong>
        <p>
          VATranscribe uses necessary storage for security and session protection. Analytics and marketing
          tracking stay disabled until you allow them.
        </p>
        <div className="cookie-consent__options">
          <label>
            <input type="checkbox" checked disabled /> Necessary
          </label>
          <label>
            <input
              type="checkbox"
              checked={draft.analytics}
              onChange={(event) => setDraft((current) => ({ ...current, analytics: event.target.checked }))}
            />{" "}
            Analytics
          </label>
          <label>
            <input
              type="checkbox"
              checked={draft.marketing}
              onChange={(event) => setDraft((current) => ({ ...current, marketing: event.target.checked }))}
            />{" "}
            Marketing
          </label>
        </div>
      </div>
      <div className="cookie-consent__actions">
        <button type="button" onClick={() => persist({ analytics: false, marketing: false })}>
          Reject optional
        </button>
        <button type="button" onClick={() => persist(draft)}>
          Save choices
        </button>
        <button type="button" onClick={() => persist({ analytics: true, marketing: false })}>
          Allow analytics
        </button>
      </div>
    </section>
  );
}
