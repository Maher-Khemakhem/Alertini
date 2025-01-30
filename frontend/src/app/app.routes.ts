import { Routes } from '@angular/router';
import { DashboardComponent } from './views/dashboard/dashboard.component';
import { NotificationsComponent } from './views/notifications/notifications.component';

export const routes: Routes = [
    {path:'',component:DashboardComponent},
    {path:'notifications',component:NotificationsComponent}
];
