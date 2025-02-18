import { Routes } from '@angular/router';
import { DashboardComponent } from './views/dashboard/dashboard.component';
import { NotificationsComponent } from './views/notifications/notifications.component';
import { LandingComponent } from './views/landing/landing.component';

export const routes: Routes = [
    {path:'',component:DashboardComponent},
    {path:'notifications',component:NotificationsComponent},
    {path:'dashboard',component:LandingComponent}
];
