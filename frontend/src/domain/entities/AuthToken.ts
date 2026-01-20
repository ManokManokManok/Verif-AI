// Domain entity representing authentication tokens
export class AuthToken {
  public readonly accessToken: string;
  public readonly refreshToken: string;
  public readonly expiresAt: Date;

  constructor(
    accessToken: string,
    refreshToken: string,
    expiresAt: Date
  ) {
    this.accessToken = accessToken;
    this.refreshToken = refreshToken;
    this.expiresAt = expiresAt;
  }

  /**
   * Check if the access token has expired
   */
  isExpired(): boolean {
    return new Date() >= this.expiresAt;
  }

  /**
   * Check if the token needs refresh (5 minutes before expiry)
   */
  needsRefresh(): boolean {
    const refreshThreshold = 5 * 60 * 1000; // 5 minutes in milliseconds
    return new Date().getTime() >= this.expiresAt.getTime() - refreshThreshold;
  }

  /**
   * Check if the token is valid (not expired and has content)
   */
  isValid(): boolean {
    return !this.isExpired() && 
           this.accessToken.trim().length > 0 && 
           this.refreshToken.trim().length > 0;
  }

  /**
   * Get remaining time in seconds before expiry
   */
  getRemainingTime(): number {
    const remaining = this.expiresAt.getTime() - new Date().getTime();
    return Math.max(0, Math.floor(remaining / 1000));
  }

  /**
   * Check if token will expire within the given number of seconds
   */
  expiresWithin(seconds: number): boolean {
    const threshold = seconds * 1000;
    const remaining = this.expiresAt.getTime() - new Date().getTime();
    return remaining <= threshold;
  }
}
