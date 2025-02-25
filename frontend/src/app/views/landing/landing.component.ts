import { Component, OnInit, ViewChild, ElementRef, AfterViewInit } from '@angular/core';
import ApexCharts from 'apexcharts';
import { CrudService } from '../../services/crud.service';
import { Chart, registerables } from 'chart.js';
import 'chartjs-chart-matrix';
import { MatrixController, MatrixElement } from 'chartjs-chart-matrix';
import { WebSocketService } from '../../services/websocket.service';
import { Subscription } from 'rxjs';
import { Router } from '@angular/router';
import { CommonModule } from '@angular/common';

Chart.register(...registerables);

export type ChartOptions = {
  series: any;
  chart: any;
  plotOptions: any;
  xaxis: any;
  yaxis: any;
  grid: any;
  stroke: any;
  tooltip: any;
  dataLabels: any;
  legend: any;
  fill: any;
  colors: string[];
  states: any;
  labels: any;
};

@Component({
  selector: 'app-landing',
  templateUrl: './landing.component.html',
  styleUrls: ['./landing.component.css'],
   imports: [CommonModule]

})
export class LandingComponent implements OnInit, AfterViewInit {
  @ViewChild('chartContainer', { static: false }) chartContainer!: ElementRef;
  @ViewChild('pieChartContainer', { static: false }) pieChartContainer!: ElementRef;
  @ViewChild('heatmapCanvas', { static: false }) heatmapCanvas!: ElementRef;

  positiveComments: number[] = [];
  negativeComments: number[] = [];
  timestamps: string[] = [];

  chart!: ApexCharts;
  pieChart!: ApexCharts;
  heatmapChart!: Chart;
  nbpos: number = 0;
  nbneg: number = 0;
  dropdownOpen = true; // Handle dropdown manually
  private wsSubscription!: Subscription;
  open = false; 
  notifications: any[] = [];
  private countSubscription!: Subscription;
  isOpen = false;
  number:any=0;
  visible=false;
  constructor(private crudservice: CrudService,private webSocketService: WebSocketService,private router:Router) {}

  ngOnInit(): void {
    this.visible = false;
    console.log(this.visible);
    this.wsSubscription = this.webSocketService.getMessages().subscribe((messages) => {
      console.log("📨 Updated Notifications:", messages);
      this.notifications = [...messages]; // Most recent messages on top
      if(this.notifications.length>0){
        this.show();
      console.log(this.visible);
      }
      
    });
    this.countSubscription = this.webSocketService.getNumber().subscribe((nb: number) => {
      this.number = nb;
    });
  }

  ngAfterViewInit(): void {
    this.initChart();
    this.initPieChart();
    this.fetchDataAndRenderChart();
  }

  fetchDataAndRenderChart(): void {
    
    
    this.crudservice.getPositiveComments().subscribe((data) => {
      this.positiveComments = data.pos || [];
      this.negativeComments = data.neg || [];
      this.timestamps = data.timestamps || [];
  
      // Compute the total positive and negative comments
      this.nbpos = this.positiveComments.reduce((acc, val) => acc + val, 0);
      this.nbneg = this.negativeComments.reduce((acc, val) => acc + val, 0);
  
      // Calculate the total number of comments
      const total = this.nbpos + this.nbneg;
  
      // Calculate the percentages
      const posPercentage = total > 0 ? (this.nbpos / total) * 100 : 0;
      const negPercentage = total > 0 ? (this.nbneg / total) * 100 : 0;
  
      // Log the percentages for debugging purposes
      console.log('Positive Percentage:', posPercentage);
      console.log('Negative Percentage:', negPercentage);
  
      // Update the pie chart data with the percentages
      this.nbpos = posPercentage;
      this.nbneg = negPercentage;
  
      if (this.timestamps.length && this.chart) {
        this.updateChart();
      }
  
      if (this.pieChart) {
        this.updatePieChart();
      }
    });
    
  }

  initChart(): void {
    if (this.chartContainer) {
      this.chart = new ApexCharts(this.chartContainer.nativeElement, {
        chart: {
          height: '100%',
          maxWidth: '100%',
          type: 'line',
          fontFamily: 'Inter, sans-serif',
          dropShadow: { enabled: false },
          toolbar: { show: false },
        },
        tooltip: { enabled: true, x: { show: false } },
        dataLabels: { enabled: false },
        stroke: { width: 6, curve: 'smooth' },
        grid: {
          show: true,
          strokeDashArray: 4,
          padding: { left: 2, right: 2, top: -26 },
        },
        series: [
          { name: 'Negative', data: [], color: '#1A56DB' },
          { name: 'Positive', data: [], color: '#7E3AF2' },
        ],
        legend: { show: false },
        xaxis: {
          categories: [],
          labels: {
            show: true,
            style: {
              fontFamily: 'Inter, sans-serif',
              cssClass: 'text-xs font-normal fill-gray-500 dark:fill-gray-400',
            },
          },
          axisBorder: { show: false },
          axisTicks: { show: false },
        },
        yaxis: { show: false },
      });
      this.chart.render();
    }
  }

  updateChart(): void {
    if (this.chart) {
      this.chart.updateOptions({
        xaxis: {
          categories: this.timestamps,
          labels: {
            rotate: -45,
            style: {
              fontSize: '12px',
              fontFamily: 'Inter, sans-serif'
            },
          },
        },
      });

      this.chart.updateSeries([
        { name: 'Negative', data: this.negativeComments },
        { name: 'Positive', data: this.positiveComments },
      ]);
    }
  }

  initPieChart(): void {
    if (this.pieChartContainer) {
      this.pieChart = new ApexCharts(this.pieChartContainer.nativeElement, {
        series: [this.nbneg, this.nbpos],
        colors: ['#1C64F2', '#16BDCA'],
        chart: { height: 420, width: '100%', type: 'pie' },
        stroke: { colors: ['white'] },
        plotOptions: { pie: { size: '100%', dataLabels: { offset: -25 } } },
        labels: ['Negative', 'Positive'], // Adjusted labels
        dataLabels: { enabled: true, style: { fontFamily: 'Inter, sans-serif' } },
        legend: { position: 'bottom', fontFamily: 'Inter, sans-serif' },
      });
      this.pieChart.render();
    }
  }

  updatePieChart(): void {
    if (this.pieChart) {
      this.pieChart.updateOptions({
        series: [this.nbneg, this.nbpos],
        labels: ['Negative', 'Positive'],
      });
    }
  }

  toggleDropdown(): void {
    this.dropdownOpen = !this.dropdownOpen;
  }
  gotonotifications(){
    this.router.navigate(["/notifications"]);;
  }
  opendropdown(){
    this.open = !this.open;
    console.log(this.open);
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
  close(){
    this.visible = false;
    console.log(this.visible);
  }
  show() {
    this.visible = true;
    setTimeout(() => this.close(), 6000); // auto close after 3 seconds
  }
}
