import { Injectable } from '@angular/core';
import { CanActivate, ActivatedRouteSnapshot, RouterStateSnapshot, Router, UrlTree } from '@angular/router';
import { Observable } from 'rxjs';

import { AuthService } from '../services/auth.service';

@Injectable({
  providedIn: 'root'
})
export class AuthGuard implements CanActivate {
  constructor(
    private authService: AuthService,
    private router: Router
  ) {}

  canActivate(
    next: ActivatedRouteSnapshot,
    state: RouterStateSnapshot
  ): Observable<boolean | UrlTree> | Promise<boolean | UrlTree> | boolean | UrlTree {
    const isLoginPage = next.data.isLoginPage || false;
    const isAuthenticated = this.authService.isAuthenticated();

    // If it's the login page and user is already authenticated, redirect to dashboard
    if (isLoginPage && isAuthenticated) {
      return this.router.createUrlTree(['/dashboard']);
    }

    // If it's a protected route and user is not authenticated, redirect to login
    if (!isLoginPage && !isAuthenticated) {
      // Store the attempted URL for redirecting after login
      this.authService.redirectUrl = state.url;
      return this.router.createUrlTree(['/login']);
    }

    return true;
  }
}
