import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class CrudService {
  private baseurl = "http://127.0.0.1:8000"
  constructor(private http: HttpClient) { }

  getarticles(): Observable<any> {
    return this.http.get<any>(`${this.baseurl}/articles/`, { withCredentials: true });
  }
}
