import { Component, OnInit } from '@angular/core';
import { CrudService } from '../../services/crud.service';

@Component({
  selector: 'app-notifications',
  imports: [],
  templateUrl: './notifications.component.html',
  styleUrl: './notifications.component.css'
})
export class NotificationsComponent implements OnInit{
  constructor(private crudservice:CrudService){}
  ngOnInit(): void {
      this.crudservice.getNotifications().subscribe((data)=>{
        console.log(data);
      })
  }
} 
