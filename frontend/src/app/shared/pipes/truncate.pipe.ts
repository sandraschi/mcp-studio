import { Pipe, PipeTransform } from '@angular/core';

@Pipe({
  name: 'truncate',
  standalone: true
})
export class TruncatePipe implements PipeTransform {
  transform(value: string, limit: number = 100, completeWords: boolean = false, ellipsis: string = '...'): string {
    if (!value || value.length <= limit) {
      return value;
    }

    if (completeWords) {
      limit = value.substr(0, limit).lastIndexOf(' ');
      if (limit === -1) {
        // No spaces found, just truncate at the limit
        return value.length > limit ? value.substr(0, limit) + ellipsis : value;
      }
    }

    return value.length > limit ? value.substr(0, limit) + ellipsis : value;
  }
}
