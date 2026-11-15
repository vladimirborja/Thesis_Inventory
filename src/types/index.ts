import type { Component } from 'vue';

export type UserRole = 'super_admin' | 'admin' | 'employee';

export interface User {
    id: number;
    name: string;
    email: string;
    role: UserRole;
    companyName?: string;
    avatarUrl?: string | null;
    canInputTransactions?: boolean;
    createdAt?: string;
}

export interface Product {
    id: number;
    name: string;
    sku: string;
    barcode?: string;
    categoryId?: number;
    categoryName?: string;
    description?: string;
    costPrice: number;
    sellingPrice: number;
    minStockLevel: number;
    quantity: number;
    unitOfMeasure: string;
    leadTimeDays?: number;
    createdAt?: string;
    images?: ProductImage[];
}

export interface ProductImage {
    id: number;
    imageUrl: string;
    createdAt?: string;
}

export interface Category {
    id: number;
    name: string;
    slug: string;
}

export interface Warehouse {
    id: number;
    name: string;
    location?: string;
}

export interface WarehouseStock {
    warehouseId: number;
    productId: number;
    quantity: number;
}

export interface Supplier {
    id: number;
    name: string;
    contactName?: string;
    email?: string;
    phone?: string;
    address?: string;
    createdAt?: string;
}

export interface StockTransaction {
    id: number;
    productId: number;
    productName: string;
    warehouseId?: number;
    warehouseName?: string;
    supplierId?: number;
    supplierName?: string;
    userId: number;
    userName: string;
    type: 'stock-in' | 'stock-out' | 'adjustment' | 'transfer';
    quantity: number;
    referenceNumber?: string;
    notes?: string;
    createdAt: string;
}

// ── Employee module ─────────────────────────────────────────────────────────

export interface Ingredient {
    id: number;
    name: string;
    quantity: number;
    unit?: string;
    minStockLevel: number;
    description?: string;
    createdAt?: string;
}

export interface SaleItem {
    id: number;
    productId: number;
    productName?: string;
    quantity: number;
    unitPrice: number;
}

export interface Sale {
    id: number;
    userId: number;
    userName?: string;
    totalAmount: number;
    paymentMethod: string;
    notes?: string;
    createdAt: string;
    items: SaleItem[];
}

export interface ActivityLog {
    id: number;
    userId: number;
    userName?: string;
    actionType: string;
    details?: Record<string, unknown>;
    createdAt: string;
}

// ── UI helpers ──────────────────────────────────────────────────────────────

export interface BreadcrumbItem {
    title: string;
    href?: string;
}

export interface NavItem {
    title: string;
    href: string;
    icon?: Component;
    children?: NavItem[];
}

// ── API response types ──────────────────────────────────────────────────────

export interface LoginResponse {
    access_token: string;
    token_type: string;
    user: User;
}

export interface DashboardSummary {
    totalUsers: number;
    totalBuy: number;
    totalSell: number;
}

export interface MonthlySalesItem {
    month: string;
    label: string;
    total: number;
}

export interface ForecastHistoryPoint {
    period: string;
    label: string;
    actual: number;
    fitted?: number | null;
}

export interface ForecastPoint {
    period: string;
    label: string;
    predicted: number;
}

export interface ProductForecast {
    productId: number;
    productName: string;
    sku: string;
    period: string;
    horizon: number;
    method: string;
    alpha?: number | null;
    mapePercent?: number | null;
    nextPeriodDemand: number;
    history: ForecastHistoryPoint[];
    forecast: ForecastPoint[];
}

export interface AbcItem {
    productId: number;
    name: string;
    sku: string;
    salesValue: number;
    valueSharePercent: number;
    cumulativePercent: number;
    abcClass: 'A' | 'B' | 'C';
}

export interface AbcAnalysis {
    items: AbcItem[];
    counts: { A: number; B: number; C: number };
}

export interface ReorderPointItem {
    itemType: 'product' | 'ingredient';
    itemId: number;
    name: string;
    sku?: string | null;
    avgDailyUsage: number;
    demandStdDev: number;
    leadTimeDays: number;
    zScore: number;
    safetyStock: number;
    reorderPoint: number;
    recommendedOrderQty: number;
    currentQuantity: number;
    minStockLevel: number;
    belowRop: boolean;
    belowMinStock: boolean;
    needsReorder: boolean;
}

export interface AnalyticsOverview {
    productsBelowRop: number;
    ingredientsBelowRop: number;
    classACount: number;
    classBCount: number;
    classCCount: number;
    avgMapePercent?: number | null;
    leadTimeDaysDefault: number;
}

/** DIMS daily-report compliance (GET /api/daily-reports/compliance) */
export interface ComplianceDayStatus {
    date: string;
    status: 'submitted' | 'draft' | 'missing' | string;
    reportId?: number | null;
    userId?: number | null;
    userName?: string | null;
    totalSales?: number | null;
    submittedAt?: string | null;
}

export interface ComplianceSummary {
    dateFrom: string;
    dateTo: string;
    expectedDays: number;
    submittedDays: number;
    draftDays: number;
    missingDays: number;
    missingRatePercent: number;
    submissionRatePercent: number;
    todayStatus: 'submitted' | 'draft' | 'missing' | string;
    days: ComplianceDayStatus[];
    missingToday: ComplianceDayStatus[];
}
