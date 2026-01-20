import { useState } from 'react';
import { X, Package, Zap, CheckCircle, AlertCircle } from 'lucide-react';
import api from '../lib/api';

interface PackageInfo {
  package_type: string;
  leads: number;
  price: number;
  display_name: string;
  price_per_lead: number;
}

interface LeadUsageSummary {
  plan_name: string;
  plan_monthly_limit: number;
  leads_used_this_month: number;
  leads_from_plan: number;
  leads_from_packages: number;
  total_available: number;
  total_remaining: number;
  usage_percentage: number;
  is_limit_reached: boolean;
  campaigns_paused: boolean;
}

interface LeadPackageModalProps {
  isOpen: boolean;
  onClose: () => void;
  onPurchaseSuccess?: () => void;
  usage?: LeadUsageSummary;
}

export default function LeadPackageModal({ 
  isOpen, 
  onClose, 
  onPurchaseSuccess,
  usage 
}: LeadPackageModalProps) {
  const [packages, setPackages] = useState<PackageInfo[]>([]);
  const [loading, setLoading] = useState(false);
  const [purchasing, setPurchasing] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  // Carregar pacotes quando modal abrir
  useState(() => {
    if (isOpen) {
      loadPackages();
    }
  });

  const loadPackages = async () => {
    try {
      setLoading(true);
      const response = await api.get('/lead-packages/available');
      setPackages(response.data.packages);
    } catch (err) {
      setError('Erro ao carregar pacotes');
    } finally {
      setLoading(false);
    }
  };

  const handlePurchase = async (packageType: string) => {
    try {
      setPurchasing(packageType);
      setError(null);
      
      // Em desenvolvimento, usa o endpoint que auto-confirma
      // Em produção, deveria redirecionar para gateway de pagamento
      const response = await api.post('/lead-packages/purchase/dev', {
        package_type: packageType,
      });
      
      setSuccess(`Pacote comprado com sucesso! ${response.data.leads_purchased} leads adicionados.`);
      
      setTimeout(() => {
        onPurchaseSuccess?.();
        onClose();
      }, 2000);
      
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Erro ao comprar pacote');
    } finally {
      setPurchasing(null);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex min-h-screen items-center justify-center p-4">
        {/* Overlay */}
        <div 
          className="fixed inset-0 bg-black bg-opacity-50 transition-opacity"
          onClick={onClose}
        />
        
        {/* Modal */}
        <div className="relative bg-white rounded-lg shadow-xl max-w-2xl w-full p-6">
          {/* Header */}
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-purple-100 rounded-lg">
                <Package className="w-6 h-6 text-purple-600" />
              </div>
              <div>
                <h2 className="text-xl font-semibold text-gray-900">
                  Pacotes de Leads
                </h2>
                <p className="text-sm text-gray-500">
                  Compre leads adicionais para suas campanhas
                </p>
              </div>
            </div>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600"
            >
              <X className="w-6 h-6" />
            </button>
          </div>

          {/* Usage Info */}
          {usage && (
            <div className={`mb-6 p-4 rounded-lg ${usage.is_limit_reached ? 'bg-red-50 border border-red-200' : 'bg-blue-50 border border-blue-200'}`}>
              <div className="flex items-center gap-2 mb-2">
                {usage.is_limit_reached ? (
                  <AlertCircle className="w-5 h-5 text-red-500" />
                ) : (
                  <Zap className="w-5 h-5 text-blue-500" />
                )}
                <span className={`font-medium ${usage.is_limit_reached ? 'text-red-700' : 'text-blue-700'}`}>
                  {usage.is_limit_reached 
                    ? 'Limite de leads atingido!' 
                    : `Você está usando ${usage.usage_percentage}% do seu limite`}
                </span>
              </div>
              <div className="text-sm text-gray-600">
                <p>Plano {usage.plan_name}: {usage.plan_monthly_limit} leads/mês</p>
                <p>Usado este mês: {usage.leads_used_this_month} leads</p>
                <p>Restante: {usage.total_remaining} leads</p>
                {usage.leads_from_packages > 0 && (
                  <p className="text-purple-600">+ {usage.leads_from_packages} leads de pacotes</p>
                )}
              </div>
              
              {/* Progress bar */}
              <div className="mt-3 h-2 bg-gray-200 rounded-full overflow-hidden">
                <div 
                  className={`h-full transition-all ${usage.usage_percentage >= 90 ? 'bg-red-500' : usage.usage_percentage >= 70 ? 'bg-yellow-500' : 'bg-green-500'}`}
                  style={{ width: `${Math.min(100, usage.usage_percentage)}%` }}
                />
              </div>
            </div>
          )}

          {/* Success Message */}
          {success && (
            <div className="mb-6 p-4 bg-green-50 border border-green-200 rounded-lg flex items-center gap-3">
              <CheckCircle className="w-5 h-5 text-green-500" />
              <span className="text-green-700">{success}</span>
            </div>
          )}

          {/* Error Message */}
          {error && (
            <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg flex items-center gap-3">
              <AlertCircle className="w-5 h-5 text-red-500" />
              <span className="text-red-700">{error}</span>
            </div>
          )}

          {/* Packages Grid */}
          {loading ? (
            <div className="text-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-600 mx-auto"></div>
              <p className="mt-2 text-gray-500">Carregando pacotes...</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {packages.map((pkg) => (
                <div
                  key={pkg.package_type}
                  className={`border-2 rounded-xl p-5 transition-all ${
                    pkg.package_type === 'leads_1000' 
                      ? 'border-purple-500 bg-purple-50 shadow-lg scale-105' 
                      : 'border-gray-200 hover:border-purple-300'
                  }`}
                >
                  {pkg.package_type === 'leads_1000' && (
                    <div className="bg-purple-500 text-white text-xs font-bold px-3 py-1 rounded-full inline-block mb-3">
                      MAIS POPULAR
                    </div>
                  )}
                  
                  <h3 className="text-lg font-semibold text-gray-900 mb-1">
                    {pkg.display_name}
                  </h3>
                  
                  <div className="flex items-baseline gap-1 mb-2">
                    <span className="text-3xl font-bold text-gray-900">
                      R${pkg.price}
                    </span>
                  </div>
                  
                  <p className="text-sm text-gray-500 mb-4">
                    R${pkg.price_per_lead.toFixed(2)} por lead
                  </p>
                  
                  <ul className="space-y-2 mb-4">
                    <li className="flex items-center gap-2 text-sm text-gray-600">
                      <CheckCircle className="w-4 h-4 text-green-500" />
                      {pkg.leads} leads adicionais
                    </li>
                    <li className="flex items-center gap-2 text-sm text-gray-600">
                      <CheckCircle className="w-4 h-4 text-green-500" />
                      Uso imediato
                    </li>
                    <li className="flex items-center gap-2 text-sm text-gray-600">
                      <CheckCircle className="w-4 h-4 text-green-500" />
                      Não expira
                    </li>
                  </ul>
                  
                  <button
                    onClick={() => handlePurchase(pkg.package_type)}
                    disabled={purchasing !== null}
                    className={`w-full py-2 px-4 rounded-lg font-medium transition-colors ${
                      pkg.package_type === 'leads_1000'
                        ? 'bg-purple-600 text-white hover:bg-purple-700'
                        : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                    } disabled:opacity-50 disabled:cursor-not-allowed`}
                  >
                    {purchasing === pkg.package_type ? (
                      <span className="flex items-center justify-center gap-2">
                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-current"></div>
                        Processando...
                      </span>
                    ) : (
                      'Comprar Agora'
                    )}
                  </button>
                </div>
              ))}
            </div>
          )}

          {/* Footer */}
          <div className="mt-6 pt-4 border-t border-gray-200 text-center text-sm text-gray-500">
            <p>
              Os leads adicionais serão somados ao seu limite mensal.
              <br />
              Dúvidas? Entre em contato com nosso suporte.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
