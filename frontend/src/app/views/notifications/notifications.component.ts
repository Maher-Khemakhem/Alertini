import { Component, OnInit, OnDestroy } from '@angular/core';
import { Subscription } from 'rxjs';
import { WebSocketService } from '../../services/websocket.service';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-notifications',
  templateUrl: './notifications.component.html',
  styleUrls: ['./notifications.component.css'],
  imports: [CommonModule]
})
export class NotificationsComponent implements OnInit, OnDestroy {
  notifications: any[] = [];
  private wsSubscription!: Subscription;
  private countSubscription!: Subscription;
  isOpen = false;
  number:any=0;
  constructor(private webSocketService: WebSocketService) {}

  ngOnInit(): void {
    this.wsSubscription = this.webSocketService.getMessages().subscribe((messages) => {
      console.log("📨 Updated Notifications:", messages);
      this.notifications = [...messages]; // Most recent messages on top
    });
    this.countSubscription = this.webSocketService.getNumber().subscribe((nb: number) => {
      this.number = nb;
    });
  }

  ngOnDestroy(): void {
    if (this.wsSubscription) {
      this.wsSubscription.unsubscribe();
      console.log("🔌 WebSocket subscription unsubscribed");
    }
  }

  toggleNotification(): void {
    this.isOpen = !this.isOpen;
  }

  removeNotification(): void {
    if (this.notifications.length > 0) {
      this.webSocketService.removeMessage(); // Remove the most recent message
    }
  }
  nulliha(){
    this.number = 0;
  }
  
}
