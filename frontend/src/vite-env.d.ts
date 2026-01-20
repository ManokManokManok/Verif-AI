/// <reference types="vite/client" />
/// <reference types="@testing-library/jest-dom" />

interface ImportMetaEnv {
  readonly VITE_API_URL: string
  readonly VITE_API_TIMEOUT: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
