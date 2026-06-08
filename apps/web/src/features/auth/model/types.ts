export type LoginRequest = {
  email: string;
  password: string;
};

export type LegalDocumentAcceptance = {
  document_type: string;
  document_version: string;
  accepted: boolean;
};

export type RegisterRequest = {
  email: string;
  password: string;
  accepted_legal_documents: LegalDocumentAcceptance[];
};

export type TokenResponse = {
  access_token: string;
  token_type: string;
};

export type CurrentUser = {
  id: string;
  email: string;
  is_active: boolean;
};
