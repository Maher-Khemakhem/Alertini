import { Component, OnInit } from '@angular/core';
import { CrudService } from '../../services/crud.service';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-dashboard',
  imports: [CommonModule],
  templateUrl: './dashboard.component.html',
  styleUrl: './dashboard.component.css'
})
export class DashboardComponent implements OnInit{
  articles:any;
  constructor(private crudservice:CrudService){}
  ngOnInit(): void {
      this.crudservice.getarticles().subscribe((data:any)=>{
        this.articles = data.articles;
        
        console.log(data);
      })
  }
}
