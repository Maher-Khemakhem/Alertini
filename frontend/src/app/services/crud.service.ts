import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable, switchMap, timer } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class CrudService {
  private baseurl = "http://127.0.0.1:8000"
  constructor(private http: HttpClient) { }

  getarticles(): Observable<any> {
    return this.http.get<any>(`${this.baseurl}/articles/`, { withCredentials: true });
  }
  getNotifications(): Observable<any> {
    return this.http.get<any>(`${this.baseurl}/notifications/`, { withCredentials: true });
  }
  getPositiveComments(): Observable<any> {
    return timer(0, 10000).pipe( // Start immediately, then every 10 seconds
      switchMap(() => this.http.get<any>(`${this.baseurl}/positive-comments/`, { withCredentials: true }))
    );
  }
  
}
