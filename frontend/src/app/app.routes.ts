import { Routes } from '@angular/router';
import { DashboardComponent } from './views/dashboard/dashboard.component';
import { LandingComponent } from './views/landing/landing.component';

export const routes: Routes = [
    {path:'',component:DashboardComponent},
    {path:'dashboard',component:LandingComponent}
];
