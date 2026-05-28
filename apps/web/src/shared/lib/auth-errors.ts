type BackendValidationItem = {
  type?: string;
  loc?: Array<string | number>;
  msg?: string;
  input?: unknown;
};

type ErrorCopy = {
  common?: {
    networkError?: string;
    requestFailed?: string;
  };
};

function normalizeFieldName(value: string): string {
  if (value === "email") return "Email";
  if (value === "password") return "Password";
  return value;
}

function isNetworkError(error: any): boolean {
  return (
    error?.code === "ERR_NETWORK" ||
    error?.message === "Network Error" ||
    (error?.request && !error?.response)
  );
}

export function extractErrorMessage(error: any, t?: ErrorCopy): string {
  if (isNetworkError(error)) {
    return (
      t?.common?.networkError ||
      "Cannot reach the API. Check that backend is running and API base URL is correct."
    );
  }

  const detail = error?.response?.data?.detail;

  if (typeof detail === "string") {
    return detail;
  }

  if (Array.isArray(detail)) {
    return detail
      .map((item: BackendValidationItem | string) => {
        if (typeof item === "string") {
          return item;
        }

        const field =
          Array.isArray(item?.loc) && item.loc.length > 0
            ? String(item.loc[item.loc.length - 1])
            : null;

        if (field && item?.msg) {
          return `${normalizeFieldName(field)}: ${item.msg}`;
        }

        if (item?.msg) {
          return item.msg;
        }

        return JSON.stringify(item);
      })
      .join("; ");
  }

  if (detail && typeof detail === "object") {
    if ("msg" in detail && typeof detail.msg === "string") {
      return detail.msg;
    }

    return JSON.stringify(detail);
  }

  return error?.message || t?.common?.requestFailed || "Request failed.";
}
