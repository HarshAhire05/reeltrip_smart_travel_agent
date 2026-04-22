# Quick Fix Guide - Missing Dependencies

## 🔧 **What Happened?**

The edit panel feature requires 2 packages that aren't installed yet:

1. **`sonner`** - Toast notification library
2. **`@radix-ui/react-alert-dialog`** - Alert dialog primitive

I've already created the UI component (`alert-dialog.tsx`) ✅

## ⚡ **Quick Fix (Choose One)**

### **Option 1: Run the Install Script (EASIEST)**

1. Navigate to: `C:\Users\PC\Desktop\reeltrip-travel\reeltrip-travel-new\frontend`
2. **Double-click:** `install-dependencies.bat`
3. Wait for installation (30-60 seconds)
4. Restart dev server: `npm run dev`

---

### **Option 2: Manual Installation**

Open your terminal in the frontend directory and run:

```bash
cd C:\Users\PC\Desktop\reeltrip-travel\reeltrip-travel-new\frontend

# Stop dev server (Ctrl+C)

# Install missing packages
npm install sonner @radix-ui/react-alert-dialog

# Restart dev server
npm run dev
```

---

## ✅ **What's Fixed?**

1. ✅ **Syntax error** in `EditTripPanel.tsx` (missing `>`)
2. ✅ **Created** `alert-dialog.tsx` component
3. ⏳ **Needs install**: `sonner` and `@radix-ui/react-alert-dialog`

---

## 🎯 **Expected Result**

After installing dependencies and restarting:

```
✓ Ready in 3s
○ Compiling /trip/[sessionId]/itinerary ...
 GET /trip/.../itinerary 200 in 2.5s
```

✨ The **floating "✏️ Edit Trip Details" button** will appear in the bottom-right corner!

---

## 📦 **Why These Packages?**

### **sonner**

- Beautiful toast notifications
- Used for showing:
  - ✅ Success: "Itinerary updated!"
  - ⚠️ Warnings: "Low budget detected"
  - ❌ Errors: "Re-plan failed"
  - ℹ️ Info: "Re-planning itinerary..."

### **@radix-ui/react-alert-dialog**

- Accessible modal dialogs
- Used for:
  - Destination change confirmation
  - "Are you sure?" prompts
  - Full rebuild warnings

Both are standard shadcn/ui dependencies.

---

## 🚀 **Next Steps**

1. **Install dependencies** (use script or manual command)
2. **Restart dev server** (`npm run dev`)
3. **Test the feature:**
   - Generate an itinerary
   - Click "View Itinerary"
   - Look for the purple floating button!
   - Click it to open the edit panel

---

## 📁 **Files Created**

✅ `frontend/components/ui/alert-dialog.tsx` - AlertDialog component  
✅ `frontend/install-dependencies.bat` - Automated installer  
✅ `frontend/QUICK_FIX.md` - This guide

---

## ❓ **Still Having Issues?**

If you see other errors after installing, check:

1. Node modules are installed: `node_modules` folder exists
2. No syntax errors in console
3. Dev server restarted successfully
4. Port 3000 isn't blocked by firewall

Need help? Check the error message in the terminal and the browser console (F12).
