import { NextRequest, NextResponse } from "next/server";

// Note: this only checks for the cookie's PRESENCE — it can't verify the JWT
// (no access to SECRET_KEY at the edge, nor should there be). Real
// authorization still happens on every API call via the backend's
// get_current_user dependency. This middleware exists purely to avoid
// flashing protected UI before an unauthenticated redirect.
const PROTECTED_PREFIXES = ["/dashboard", "/jobs", "/resume", "/analytics", "/learning", "/interview-prep"];

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;
  const isProtected = PROTECTED_PREFIXES.some((p) => pathname.startsWith(p));

  if (!isProtected) return NextResponse.next();

  const hasRefreshCookie = request.cookies.has("refresh_token");
  if (!hasRefreshCookie) {
    const loginUrl = new URL("/login", request.url);
    loginUrl.searchParams.set("redirect", pathname);
    return NextResponse.redirect(loginUrl);
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/dashboard/:path*", "/jobs/:path*", "/resume/:path*", "/analytics/:path*", "/learning/:path*", "/interview-prep/:path*"],
};
