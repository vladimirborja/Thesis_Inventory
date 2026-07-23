import type { Component } from 'vue';

export type UserRole = 'super_admin' | 'admin' | 'employee';

export interface User {
    id: number;
    name: string;
    email: string;
    role: UserRole;
    companyName?: string;
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
