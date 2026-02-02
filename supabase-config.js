// Supabase Configuration
const SUPABASE_URL = 'https://cjttjcarpqwonxixtovk.supabase.co';
const SUPABASE_ANON_KEY = 'sb_publishable_Zt9fG5IJ_zau6bW3I4tz9g_cXCN7bnn';

// Initialize Supabase client
const supabase = window.supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY);

// Fetch orders from Supabase
async function fetchOrdersFromSupabase() {
  const { data, error } = await supabase
    .from('orders')
    .select('*')
    .order('order_date', { ascending: false });
  
  if (error) {
    console.error('Error fetching orders:', error);
    return null;
  }
  return data;
}

// Fetch inventory from Supabase
async function fetchInventoryFromSupabase() {
  const { data, error } = await supabase
    .from('inventory')
    .select('*');
  
  if (error) {
    console.error('Error fetching inventory:', error);
    return null;
  }
  return data;
}

// Fetch last sync log
async function fetchLastSync() {
  const { data, error } = await supabase
    .from('sync_logs')
    .select('*')
    .order('created_at', { ascending: false })
    .limit(1);
  
  if (error) {
    console.error('Error fetching sync log:', error);
    return null;
  }
  return data?.[0];
}

// Trigger manual sync (calls Edge Function)
async function triggerManualSync() {
  try {
    const response = await fetch(`${SUPABASE_URL}/functions/v1/sync-orders`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${SUPABASE_ANON_KEY}`,
        'Content-Type': 'application/json'
      }
    });
    
    if (!response.ok) {
      throw new Error('Sync failed');
    }
    
    return await response.json();
  } catch (error) {
    console.error('Manual sync error:', error);
    throw error;
  }
}

export { supabase, fetchOrdersFromSupabase, fetchInventoryFromSupabase, fetchLastSync, triggerManualSync };
