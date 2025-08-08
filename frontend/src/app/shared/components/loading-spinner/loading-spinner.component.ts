import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';

@Component({
  selector: 'app-loading-spinner',
  templateUrl: './loading-spinner.component.html',
  styleUrls: ['./loading-spinner.component.scss'],
  standalone: true,
  imports: [
    CommonModule,
    MatProgressSpinnerModule
  ]
})
export class LoadingSpinnerComponent {
  @Input() diameter = 40;
  @Input() strokeWidth = 4;
  @Input() message = 'Loading...';
  @Input() overlay = false;
  @Input() fullScreen = false;
}
