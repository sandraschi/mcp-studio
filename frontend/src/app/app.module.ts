import { NgModule } from '@angular/core';
import { BrowserModule } from '@angular/platform-browser';
import { BrowserAnimationsModule } from '@angular/platform-browser/animations';
import { HttpClientModule, HTTP_INTERCEPTORS } from '@angular/common/http';

// App Routing
import { AppRoutingModule } from './app-routing.module';

// Core Modules
import { CoreModule } from './core/core.module';
import { SharedModule } from './shared/shared.module';

// Feature Modules
import { DashboardModule } from './dashboard/dashboard.module';

// Main App Component
import { AppComponent } from './app.component';

// HTTP Interceptors
import { AuthInterceptor } from './core/interceptors/auth.interceptor';
import { ErrorInterceptor } from './core/interceptors/error.interceptor';
import { LoadingInterceptor } from './core/interceptors/loading.interceptor';

// Angular Material
import { MatSidenavModule } from '@angular/material/sidenav';
import { MatToolbarModule } from '@angular/material/toolbar';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatTooltipModule } from '@angular/material/tooltip';

// NgBootstrap
import { NgbModule } from '@ng-bootstrap/ng-bootstrap';

// Icons
import { IconsModule } from './core/icons/icons.module';

// Components
import { ServerDashboardComponent } from './server-dashboard/server-dashboard.component';
import { ServerDetailComponent } from './server-detail/server-detail.component';

@NgModule({
  declarations: [
    AppComponent,
    ServerDashboardComponent,
    ServerDetailComponent
  ],
  imports: [
    // Angular Modules
    BrowserModule,
    BrowserAnimationsModule,
    HttpClientModule,
    
    // App Routing
    AppRoutingModule,
    
    // Core & Shared Modules
    CoreModule,
    SharedModule,
    
    // Feature Modules
    DashboardModule,
    
    // Angular Material
    MatSidenavModule,
    MatToolbarModule,
    MatIconModule,
    MatButtonModule,
    MatCardModule,
    MatProgressSpinnerModule,
    MatTooltipModule,
    
    // NgBootstrap
    NgbModule,
    
    // Icons
    IconsModule
  ],
  providers: [
    { provide: HTTP_INTERCEPTORS, useClass: AuthInterceptor, multi: true },
    { provide: HTTP_INTERCEPTORS, useClass: ErrorInterceptor, multi: true },
    { provide: HTTP_INTERCEPTORS, useClass: LoadingInterceptor, multi: true }
  ],
  bootstrap: [AppComponent]
})
export class AppModule { }
