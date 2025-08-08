import { Injectable } from '@angular/core';
import { HttpRequest, HttpHandler, HttpEvent, HttpInterceptor, HttpErrorResponse } from '@angular/common/http';
import { Observable, throwError } from 'rxjs';
import { catchError } from 'rxjs/operators';
import { Router } from '@angular/router';
import { MatSnackBar } from '@angular/material/snack-bar';

@Injectable()
export class ErrorInterceptor implements HttpInterceptor {
  constructor(
    private router: Router,
    private snackBar: MatSnackBar
  ) {}

  intercept(request: HttpRequest<any>, next: HttpHandler): Observable<HttpEvent<any>> {
    return next.handle(request).pipe(
      catchError((error: HttpErrorResponse) => {
        let errorMessage = 'An error occurred';
        let errorDetails = '';
        
        if (error.error instanceof ErrorEvent) {
          // Client-side error
          errorMessage = `Error: ${error.error.message}`;
        } else {
          // Server-side error
          errorMessage = `Error Code: ${error.status}\nMessage: ${error.message}`;
          
          // Handle specific error statuses
          switch (error.status) {
            case 400: // Bad Request
              errorDetails = this.handleBadRequest(error);
              break;
            case 401: // Unauthorized
              return this.handleUnauthorized(error);
            case 403: // Forbidden
              errorDetails = 'You do not have permission to perform this action.';
              this.router.navigate(['/forbidden']);
              break;
            case 404: // Not Found
              errorDetails = 'The requested resource was not found.';
              this.router.navigate(['/not-found']);
              break;
            case 500: // Internal Server Error
              errorDetails = 'An internal server error occurred. Please try again later.';
              break;
            case 503: // Service Unavailable
              errorDetails = 'The service is currently unavailable. Please try again later.';
              break;
            default:
              errorDetails = error.message || 'An unexpected error occurred.';
          }
        }
        
        // Show error message to user
        this.showErrorMessage(errorDetails || errorMessage);
        
        // Log the error for debugging
        console.error('HTTP Error:', error);
        
        // Re-throw the error for further handling if needed
        return throwError(() => new Error(errorMessage));
      })
    );
  }
  
  private handleBadRequest(error: HttpErrorResponse): string {
    // Handle validation errors (typically 400 with a specific structure)
    if (error.error && typeof error.error === 'object') {
      if (error.error.errors) {
        // Handle validation errors from ASP.NET Core
        return this.formatValidationErrors(error.error.errors);
      } else if (error.error.message) {
        // Handle custom error message
        return error.error.message;
      }
    }
    return error.error?.message || 'Invalid request. Please check your input.';
  }
  
  private handleUnauthorized(error: HttpErrorResponse): Observable<never> {
    // The AuthInterceptor will handle 401 by trying to refresh the token
    // If we get here, token refresh failed or was not possible
    return throwError(() => new Error('Authentication failed. Please log in again.'));
  }
  
  private formatValidationErrors(errors: { [key: string]: string[] }): string {
    let message = 'Validation failed:\n';
    for (const key in errors) {
      if (errors.hasOwnProperty(key)) {
        message += `- ${key}: ${errors[key].join(', ')}\n`;
      }
    }
    return message;
  }
  
  private showErrorMessage(message: string): void {
    this.snackBar.open(message, 'Dismiss', {
      duration: 5000,
      horizontalPosition: 'right',
      verticalPosition: 'top',
      panelClass: ['error-snackbar']
    });
  }
}
