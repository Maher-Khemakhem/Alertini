import { Injectable, OnDestroy } from '@angular/core';
import { Observable, BehaviorSubject } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class WebSocketService implements OnDestroy {
  private socket!: WebSocket;
  // Using unshift/shift so that the newest message is at the beginning.
  private messagesStack: any[] = [];
  private messagesSubject: BehaviorSubject<any[]> = new BehaviorSubject<any[]>([]);
  private numberSubject: BehaviorSubject<number> = new BehaviorSubject<number>(0);
  private reconnectInterval = 5000; // 5 seconds

  constructor() {
    this.connect();
    this.reconnect();
  }

  /**
   * Establish the WebSocket connection.
   */
  private connect(): void {
    this.socket = new WebSocket("ws://127.0.0.1:8000/ws/notifications/");

    this.socket.onopen = () => {
      console.log("✅ WebSocket connected!");
    };

    this.socket.onmessage = (event) => {
      console.log("📩 Raw WebSocket message received:", event.data);

      try {
        const data = JSON.parse(event.data); // Parse JSON message

        if (!this.messageExists(data)) {
          // Prepend new message so the newest is at the top.
          this.messagesStack.unshift(data);
          // Emit the updated stack.
          this.messagesSubject.next([...this.messagesStack]);
          // Update the count.
          this.numberSubject.next(this.messagesStack.length);
        } else {
          console.log("⚠️ Duplicate message ignored:", data);
        }
      } catch (error) {
        console.error("❌ Invalid JSON received:", event.data, error);
      }
    };

    this.socket.onerror = (error) => {
      console.error("❌ WebSocket error:", error);
      this.reconnect();
    };

    this.socket.onclose = (event) => {
      console.warn(
        `⚠️ WebSocket closed (Code: ${event.code}, Reason: ${event.reason}). Reconnecting in ${this.reconnectInterval / 1000}s...`
      );
      this.reconnect();
    };
  }

  /**
   * Check if a message already exists in the stack (deep equality check).
   */
  private messageExists(newMessage: any): boolean {
    return this.messagesStack.some(msg => this.isEqual(msg, newMessage));
  }

  /**
   * Perform a deep equality check using JSON.stringify.
   */
  private isEqual(obj1: any, obj2: any): boolean {
    return JSON.stringify(obj1) === JSON.stringify(obj2);
  }

  /**
   * Attempt to reconnect after a specified interval.
   */
  private reconnect(): void {
    if (this.socket) {
      this.socket.close(); // Ensure the old socket is closed
    }
  
    setTimeout(() => {
      console.log("🔄 Attempting to reconnect WebSocket...");
      this.connect();
    }, this.reconnectInterval);
  }
  

  /**
   * Returns an observable of the current message stack.
   */
  getMessages(): Observable<any[]> {
    return this.messagesSubject.asObservable();
  }

  /**
   * Returns an observable of the number of notifications.
   */
  getNumber(): Observable<number> {
    return this.numberSubject.asObservable();
  }

  /**
   * Send a message via WebSocket.
   */
  sendMessage(message: any): void {
    if (this.socket && this.socket.readyState === WebSocket.OPEN) {
      this.socket.send(JSON.stringify(message));
    } else {
      console.error("❌ WebSocket is not open. Cannot send message.");
    }
  }

  /**
   * Remove the most recent (top) message after it's processed.
   */
  removeMessage(): void {
    if (this.messagesStack.length > 0) {
      this.messagesStack.shift(); // Remove the first element (newest message).
      this.messagesSubject.next([...this.messagesStack]);
      this.numberSubject.next(this.messagesStack.length);
    }
  }

  /**
   * Cleanup the WebSocket connection when the service is destroyed.
   */
  ngOnDestroy(): void {
    if (this.socket) {
      this.socket.close();
      console.log("❌ WebSocket connection closed.");
    }
  }
}
