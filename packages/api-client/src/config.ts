export interface ApiClientConfig {
  getBaseUrl: () => string;
  getToken: () => string | null;
  onUnauthorized?: () => void;
  /** For resolving relative API paths when parsing full URLs */
  getOrigin?: () => string;
}

let clientConfig: ApiClientConfig | null = null;

export function configureApiClient(config: ApiClientConfig): void {
  clientConfig = config;
}

export function getApiClientConfig(): ApiClientConfig {
  if (!clientConfig) {
    throw new Error("ApiClient not configured. Call configureApiClient() first.");
  }
  return clientConfig;
}

export function getApiBase(): string {
  return getApiClientConfig().getBaseUrl();
}
