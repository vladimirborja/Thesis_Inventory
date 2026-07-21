import { defineStore } from 'pinia';
import { ref } from 'vue';
import type { User, UserRole, Product, Category, Warehouse, Supplier, StockTransaction } from '@/types';

export const useAuthStore = defineStore('auth', () => {
    // Current user state
    const currentUser = ref<User | null>(null);

    // Mock Users
    const users = ref<User[]>([
        { id: 1, name: 'John Doe', email: 'superadmin@foodprocessing.com', role: 'super_admin', companyName: 'Apex Food Processing Corp' },
        { id: 2, name: 'Alice Smith', email: 'admin@foodprocessing.com', role: 'admin', companyName: 'Apex Food Processing Corp' },
        { id: 3, name: 'Bob Johnson', email: 'employee@foodprocessing.com', role: 'employee', companyName: 'Apex Food Processing Corp' }
    ]);

    // Mock Categories
    const categories = ref<Category[]>([
        { id: 1, name: 'Raw Ingredients', slug: 'raw-ingredients' },
        { id: 2, name: 'Packaging Materials', slug: 'packaging-materials' },
        { id: 3, name: 'Finished Goods', slug: 'finished-goods' },
        { id: 4, name: 'Additives & Preservatives', slug: 'additives-preservatives' }
    ]);

    // Mock Warehouses
    const warehouses = ref<Warehouse[]>([
        { id: 1, name: 'Central Cold Storage', location: 'Section A - Temperature Controlled' },
        { id: 2, name: 'Raw Materials Depot', location: 'Warehouse 3, Bay B' },
        { id: 3, name: 'Packaging Storehouse', location: 'Warehouse 1, Floor 2' },
        { id: 4, name: 'Finished Goods Yard', location: 'Loading Bay 5' }
    ]);

    // Mock Suppliers
    const suppliers = ref<Supplier[]>([
        { id: 1, name: 'Agri-Grow Farms Inc.', contactName: 'Robert Vance', email: 'vance@agrigrow.com', phone: '+63 905 123 4567', address: 'Davao City, Philippines' },
        { id: 2, name: 'PolyPack Plastics Ltd.', contactName: 'Sarah Jenkins', email: 'sjenkins@polypack.com', phone: '+63 917 987 6543', address: 'Valenzuela City, Philippines' },
        { id: 3, name: 'Global Additives Co.', contactName: 'Dr. Ken Suzuki', email: 'suzuki@globaladditives.com', phone: '+81 3 5555 0192', address: 'Tokyo, Japan' }
    ]);

    // Mock Products
    const products = ref<Product[]>([
        { id: 101, name: 'Premium Semolina Wheat Flour', sku: 'RM-FLOUR-001', barcode: '4801234567011', categoryId: 1, categoryName: 'Raw Ingredients', description: 'High gluten flour for pasta processing', costPrice: 35.00, sellingPrice: 50.00, minStockLevel: 100, quantity: 450, unitOfMeasure: 'bags (25kg)' },
        { id: 102, name: 'BPA-Free Vacuum Sealing Film', sku: 'PK-FILM-002', barcode: '4801234567028', categoryId: 2, categoryName: 'Packaging Materials', description: '200mm barrier roll for meat packaging', costPrice: 150.00, sellingPrice: 220.00, minStockLevel: 20, quantity: 12, unitOfMeasure: 'rolls (100m)' },
        { id: 103, name: 'Canned Tomato Paste Concentrated', sku: 'RM-TPAS-003', barcode: '4801234567035', categoryId: 1, categoryName: 'Raw Ingredients', description: 'Concentrated paste, Brix 28-30%', costPrice: 85.00, sellingPrice: 120.00, minStockLevel: 50, quantity: 3, unitOfMeasure: 'drums (50kg)' },
        { id: 104, name: 'Natural Cane Sugar Refined', sku: 'RM-SUGR-004', barcode: '4801234567042', categoryId: 1, categoryName: 'Raw Ingredients', description: 'Pure cane sugar, fine grade', costPrice: 45.00, sellingPrice: 60.00, minStockLevel: 200, quantity: 180, unitOfMeasure: 'bags (50kg)' },
        { id: 105, name: 'Organic Citric Acid Powder', sku: 'AD-CITR-005', barcode: '4801234567059', categoryId: 4, categoryName: 'Additives & Preservatives', description: 'USP/FCC grade food acidulant', costPrice: 95.00, sellingPrice: 140.00, minStockLevel: 30, quantity: 45, unitOfMeasure: 'bags (25kg)' },
        { id: 106, name: 'Sweet Chilli Sauce (Finished)', sku: 'FG-CHLI-006', barcode: '4801234567066', categoryId: 3, categoryName: 'Finished Goods', description: 'Bottled sweet chilli sauce ready for retail', costPrice: 22.00, sellingPrice: 38.00, minStockLevel: 500, quantity: 1250, unitOfMeasure: 'cases (24x250ml)' }
    ]);

    // Mock Stock Transactions
    const transactions = ref<StockTransaction[]>([
        { id: 1, productId: 101, productName: 'Premium Semolina Wheat Flour', warehouseId: 2, warehouseName: 'Raw Materials Depot', userId: 2, userName: 'Alice Smith', type: 'stock-in', quantity: 200, referenceNumber: 'PO-2026-001', notes: 'Initial receipt from Agri-Grow Farms', createdAt: '2026-07-10 09:30:00' },
        { id: 2, productId: 103, productName: 'Canned Tomato Paste Concentrated', warehouseId: 1, warehouseName: 'Central Cold Storage', userId: 3, userName: 'Bob Johnson', type: 'stock-out', quantity: 15, referenceNumber: 'WO-2026-042', notes: 'Released for Batch 4 Sauce Production', createdAt: '2026-07-12 14:15:00' },
        { id: 3, productId: 102, productName: 'BPA-Free Vacuum Sealing Film', warehouseId: 3, warehouseName: 'Packaging Storehouse', userId: 2, userName: 'Alice Smith', type: 'adjustment', quantity: -2, referenceNumber: 'ADJ-009', notes: 'Damaged during forklift maneuver', createdAt: '2026-07-13 11:00:00' }
    ]);

    // Login function
    function login(email: string, role: UserRole) {
        // Find existing user or create one
        let user = users.value.find(u => u.email === email && u.role === role);
        if (!user) {
            const prefix = email.split('@')[0] || 'USER';
            user = {
                id: Date.now(),
                name: prefix.toUpperCase(),
                email,
                role,
                companyName: 'Apex Food Processing Corp'
            };
            users.value.push(user);
        }
        currentUser.value = user;
        localStorage.setItem('ims_user', JSON.stringify(user));
    }

    // Register function
    function register(name: string, email: string, role: UserRole, companyName: string) {
        const newUser: User = {
            id: Date.now(),
            name,
            email,
            role,
            companyName
        };
        users.value.push(newUser);
        currentUser.value = newUser;
        localStorage.setItem('ims_user', JSON.stringify(newUser));
    }

    // Logout function
    function logout() {
        currentUser.value = null;
        localStorage.removeItem('ims_user');
    }

    // Initialize from localStorage if exists
    function initSession() {
        const stored = localStorage.getItem('ims_user');
        if (stored) {
            try {
                currentUser.value = JSON.parse(stored);
            } catch (e) {
                currentUser.value = null;
            }
        }
    }


    return {
        currentUser,
        users,
        categories,
        warehouses,
        suppliers,
        products,
        transactions,
        login,
        register,
        logout,
        initSession
    };
});
