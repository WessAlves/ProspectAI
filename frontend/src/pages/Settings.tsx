import { useState, useEffect } from 'react';
import { 
  User, 
  Building2, 
  Lock, 
  CreditCard, 
  Check, 
  AlertCircle,
  Eye,
  EyeOff,
  Loader2
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { useToast } from '@/components/ui/use-toast';
import { useAuthStore } from '@/stores/authStore';
import api from '@/lib/api';
import {
  validateCPF,
  validateCNPJ,
  formatCPF,
  formatCNPJ,
  formatPhone,
  formatCEP,
  formatCardNumber,
  detectCardBrand,
  validateCardNumber,
  BRAZILIAN_STATES,
} from '@/lib/validators';

interface ProfileData {
  id: string;
  email: string;
  full_name: string;
  profile_completed: boolean;
  person_type: 'individual' | 'company' | null;
  phone: string | null;
  // Pessoa Física
  cpf: string | null;
  birth_date: string | null;
  first_name: string | null;
  last_name: string | null;
  // Pessoa Jurídica
  cnpj: string | null;
  company_name: string | null;
  trade_name: string | null;
  state_registration: string | null;
  municipal_registration: string | null;
  // Endereço
  address_street: string | null;
  address_number: string | null;
  address_complement: string | null;
  address_neighborhood: string | null;
  address_city: string | null;
  address_state: string | null;
  address_zip_code: string | null;
  // Pagamento
  has_payment_method: boolean;
  card_last_four: string | null;
  card_brand: string | null;
}

interface PaymentMethod {
  has_payment_method: boolean;
  card_last_four: string | null;
  card_brand: string | null;
  exp_month: number | null;
  exp_year: number | null;
  billing_name: string | null;
}

export default function Settings() {
  const { toast } = useToast();
  const { refreshUser } = useAuthStore();
  
  const [activeTab, setActiveTab] = useState('profile');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [profile, setProfile] = useState<ProfileData | null>(null);
  const [paymentMethod, setPaymentMethod] = useState<PaymentMethod | null>(null);
  
  // Form states
  const [personType, setPersonType] = useState<'individual' | 'company'>('individual');
  
  // Pessoa Física
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [cpf, setCpf] = useState('');
  const [birthDate, setBirthDate] = useState('');
  
  // Pessoa Jurídica
  const [cnpj, setCnpj] = useState('');
  const [companyName, setCompanyName] = useState('');
  const [tradeName, setTradeName] = useState('');
  const [stateRegistration, setStateRegistration] = useState('');
  const [municipalRegistration, setMunicipalRegistration] = useState('');
  
  // Comum
  const [phone, setPhone] = useState('');
  
  // Endereço
  const [addressStreet, setAddressStreet] = useState('');
  const [addressNumber, setAddressNumber] = useState('');
  const [addressComplement, setAddressComplement] = useState('');
  const [addressNeighborhood, setAddressNeighborhood] = useState('');
  const [addressCity, setAddressCity] = useState('');
  const [addressState, setAddressState] = useState('');
  const [addressZipCode, setAddressZipCode] = useState('');
  
  // Senha
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showCurrentPassword, setShowCurrentPassword] = useState(false);
  const [showNewPassword, setShowNewPassword] = useState(false);
  const [changingPassword, setChangingPassword] = useState(false);
  
  // Cartão
  const [cardNumber, setCardNumber] = useState('');
  const [cardHolder, setCardHolder] = useState('');
  const [cardExpMonth, setCardExpMonth] = useState('');
  const [cardExpYear, setCardExpYear] = useState('');
  const [cardCvv, setCardCvv] = useState('');
  const [savingCard, setSavingCard] = useState(false);
  
  // Erros de validação
  const [errors, setErrors] = useState<Record<string, string>>({});

  useEffect(() => {
    loadProfile();
    loadPaymentMethod();
  }, []);

  useEffect(() => {
    if (profile) {
      setPersonType(profile.person_type || 'individual');
      setFirstName(profile.first_name || '');
      setLastName(profile.last_name || '');
      setCpf(profile.cpf || '');
      setBirthDate(profile.birth_date || '');
      setCnpj(profile.cnpj || '');
      setCompanyName(profile.company_name || '');
      setTradeName(profile.trade_name || '');
      setStateRegistration(profile.state_registration || '');
      setMunicipalRegistration(profile.municipal_registration || '');
      setPhone(profile.phone || '');
      setAddressStreet(profile.address_street || '');
      setAddressNumber(profile.address_number || '');
      setAddressComplement(profile.address_complement || '');
      setAddressNeighborhood(profile.address_neighborhood || '');
      setAddressCity(profile.address_city || '');
      setAddressState(profile.address_state || '');
      setAddressZipCode(profile.address_zip_code || '');
    }
  }, [profile]);

  const loadProfile = async () => {
    try {
      const response = await api.get('/user/profile');
      setProfile(response.data);
    } catch (error) {
      toast({
        title: 'Erro',
        description: 'Não foi possível carregar o perfil',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  const loadPaymentMethod = async () => {
    try {
      const response = await api.get('/user/payment-method');
      setPaymentMethod(response.data);
    } catch (error) {
      console.error('Erro ao carregar método de pagamento:', error);
    }
  };

  const validateIndividualForm = (): boolean => {
    const newErrors: Record<string, string> = {};
    
    if (!firstName.trim()) newErrors.firstName = 'Nome é obrigatório';
    if (!lastName.trim()) newErrors.lastName = 'Sobrenome é obrigatório';
    
    if (!cpf.trim()) {
      newErrors.cpf = 'CPF é obrigatório';
    } else if (!validateCPF(cpf)) {
      newErrors.cpf = 'CPF inválido';
    }
    
    if (!birthDate) {
      newErrors.birthDate = 'Data de nascimento é obrigatória';
    } else {
      const birth = new Date(birthDate);
      const today = new Date();
      const age = today.getFullYear() - birth.getFullYear();
      if (age < 18) newErrors.birthDate = 'Você deve ter pelo menos 18 anos';
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const validateCompanyForm = (): boolean => {
    const newErrors: Record<string, string> = {};
    
    if (!firstName.trim()) newErrors.firstName = 'Nome do responsável é obrigatório';
    if (!lastName.trim()) newErrors.lastName = 'Sobrenome do responsável é obrigatório';
    
    if (!cnpj.trim()) {
      newErrors.cnpj = 'CNPJ é obrigatório';
    } else if (!validateCNPJ(cnpj)) {
      newErrors.cnpj = 'CNPJ inválido';
    }
    
    if (!companyName.trim()) newErrors.companyName = 'Razão Social é obrigatória';
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSaveProfile = async () => {
    if (personType === 'individual') {
      if (!validateIndividualForm()) return;
      
      setSaving(true);
      try {
        await api.put('/user/profile/individual', {
          person_type: 'individual',
          first_name: firstName,
          last_name: lastName,
          cpf: cpf.replace(/\D/g, ''),
          birth_date: birthDate,
          phone: phone.replace(/\D/g, '') || null,
          address_street: addressStreet || null,
          address_number: addressNumber || null,
          address_complement: addressComplement || null,
          address_neighborhood: addressNeighborhood || null,
          address_city: addressCity || null,
          address_state: addressState || null,
          address_zip_code: addressZipCode.replace(/\D/g, '') || null,
        });
        
        toast({
          title: 'Sucesso',
          description: 'Perfil atualizado com sucesso!',
        });
        
        await loadProfile();
        await refreshUser();
      } catch (error: any) {
        toast({
          title: 'Erro',
          description: error.response?.data?.detail || 'Erro ao salvar perfil',
          variant: 'destructive',
        });
      } finally {
        setSaving(false);
      }
    } else {
      if (!validateCompanyForm()) return;
      
      setSaving(true);
      try {
        await api.put('/user/profile/company', {
          person_type: 'company',
          cnpj: cnpj.replace(/\D/g, ''),
          company_name: companyName,
          trade_name: tradeName || null,
          state_registration: stateRegistration || null,
          municipal_registration: municipalRegistration || null,
          first_name: firstName,
          last_name: lastName,
          phone: phone.replace(/\D/g, '') || null,
          address_street: addressStreet || null,
          address_number: addressNumber || null,
          address_complement: addressComplement || null,
          address_neighborhood: addressNeighborhood || null,
          address_city: addressCity || null,
          address_state: addressState || null,
          address_zip_code: addressZipCode.replace(/\D/g, '') || null,
        });
        
        toast({
          title: 'Sucesso',
          description: 'Perfil atualizado com sucesso!',
        });
        
        await loadProfile();
        await refreshUser();
      } catch (error: any) {
        toast({
          title: 'Erro',
          description: error.response?.data?.detail || 'Erro ao salvar perfil',
          variant: 'destructive',
        });
      } finally {
        setSaving(false);
      }
    }
  };

  const handleChangePassword = async () => {
    const newErrors: Record<string, string> = {};
    
    if (!currentPassword) newErrors.currentPassword = 'Senha atual é obrigatória';
    if (!newPassword) newErrors.newPassword = 'Nova senha é obrigatória';
    else if (newPassword.length < 6) newErrors.newPassword = 'Mínimo 6 caracteres';
    if (newPassword !== confirmPassword) newErrors.confirmPassword = 'As senhas não coincidem';
    
    setErrors(newErrors);
    if (Object.keys(newErrors).length > 0) return;
    
    setChangingPassword(true);
    try {
      await api.put('/user/password', {
        current_password: currentPassword,
        new_password: newPassword,
        confirm_password: confirmPassword,
      });
      
      toast({
        title: 'Sucesso',
        description: 'Senha alterada com sucesso!',
      });
      
      setCurrentPassword('');
      setNewPassword('');
      setConfirmPassword('');
    } catch (error: any) {
      toast({
        title: 'Erro',
        description: error.response?.data?.detail || 'Erro ao alterar senha',
        variant: 'destructive',
      });
    } finally {
      setChangingPassword(false);
    }
  };

  const handleSaveCard = async () => {
    const newErrors: Record<string, string> = {};
    
    if (!cardNumber) {
      newErrors.cardNumber = 'Número do cartão é obrigatório';
    } else if (!validateCardNumber(cardNumber)) {
      newErrors.cardNumber = 'Número do cartão inválido';
    }
    
    if (!cardHolder) newErrors.cardHolder = 'Nome no cartão é obrigatório';
    if (!cardExpMonth) newErrors.cardExpMonth = 'Mês é obrigatório';
    if (!cardExpYear) newErrors.cardExpYear = 'Ano é obrigatório';
    if (!cardCvv) newErrors.cardCvv = 'CVV é obrigatório';
    else if (cardCvv.length < 3) newErrors.cardCvv = 'CVV inválido';
    
    setErrors(newErrors);
    if (Object.keys(newErrors).length > 0) return;
    
    setSavingCard(true);
    try {
      await api.post('/user/payment-method', {
        card_number: cardNumber.replace(/\s/g, ''),
        card_holder_name: cardHolder,
        exp_month: parseInt(cardExpMonth),
        exp_year: parseInt(cardExpYear),
        cvv: cardCvv,
      });
      
      toast({
        title: 'Sucesso',
        description: 'Cartão adicionado com sucesso!',
      });
      
      setCardNumber('');
      setCardHolder('');
      setCardExpMonth('');
      setCardExpYear('');
      setCardCvv('');
      
      await loadPaymentMethod();
    } catch (error: any) {
      toast({
        title: 'Erro',
        description: error.response?.data?.detail || 'Erro ao adicionar cartão',
        variant: 'destructive',
      });
    } finally {
      setSavingCard(false);
    }
  };

  const handleRemoveCard = async () => {
    if (!confirm('Tem certeza que deseja remover o cartão?')) return;
    
    try {
      await api.delete('/user/payment-method');
      
      toast({
        title: 'Sucesso',
        description: 'Cartão removido com sucesso!',
      });
      
      setPaymentMethod(null);
    } catch (error: any) {
      toast({
        title: 'Erro',
        description: error.response?.data?.detail || 'Erro ao remover cartão',
        variant: 'destructive',
      });
    }
  };

  const getCardBrandIcon = (brand: string) => {
    const icons: Record<string, string> = {
      visa: '💳 Visa',
      mastercard: '💳 Mastercard',
      amex: '💳 American Express',
      elo: '💳 Elo',
      hipercard: '💳 Hipercard',
      diners: '💳 Diners',
      discover: '💳 Discover',
      unknown: '💳 Cartão',
    };
    return icons[brand] || icons.unknown;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
      </div>
    );
  }

  return (
    <div className="container mx-auto py-6 max-w-4xl">
      <div className="mb-6">
        <h1 className="text-3xl font-bold">Configurações</h1>
        <p className="text-muted-foreground">
          Gerencie seu perfil, segurança e métodos de pagamento
        </p>
      </div>

      {!profile?.profile_completed && (
        <div className="mb-6 p-4 bg-amber-50 border border-amber-200 rounded-lg flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-amber-600 mt-0.5" />
          <div>
            <p className="font-medium text-amber-800">Complete seu cadastro</p>
            <p className="text-sm text-amber-700">
              Para utilizar todas as funcionalidades da plataforma, complete seu perfil informando seus dados pessoais ou empresariais.
            </p>
          </div>
        </div>
      )}

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-3 mb-6">
          <TabsTrigger value="profile" className="flex items-center gap-2">
            <User className="w-4 h-4" />
            Perfil
          </TabsTrigger>
          <TabsTrigger value="security" className="flex items-center gap-2">
            <Lock className="w-4 h-4" />
            Segurança
          </TabsTrigger>
          <TabsTrigger value="payment" className="flex items-center gap-2">
            <CreditCard className="w-4 h-4" />
            Pagamento
          </TabsTrigger>
        </TabsList>

        {/* Tab: Perfil */}
        <TabsContent value="profile">
          <Card>
            <CardHeader>
              <CardTitle>Informações do Perfil</CardTitle>
              <CardDescription>
                Atualize seus dados pessoais ou empresariais
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Tipo de Pessoa */}
              <div className="space-y-3">
                <Label>Tipo de Cadastro</Label>
                <div className="flex gap-4">
                  <Button
                    type="button"
                    variant={personType === 'individual' ? 'default' : 'outline'}
                    className="flex-1"
                    onClick={() => setPersonType('individual')}
                  >
                    <User className="w-4 h-4 mr-2" />
                    Pessoa Física
                  </Button>
                  <Button
                    type="button"
                    variant={personType === 'company' ? 'default' : 'outline'}
                    className="flex-1"
                    onClick={() => setPersonType('company')}
                  >
                    <Building2 className="w-4 h-4 mr-2" />
                    Pessoa Jurídica
                  </Button>
                </div>
              </div>

              {personType === 'individual' ? (
                /* Formulário Pessoa Física */
                <>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label htmlFor="firstName">Nome *</Label>
                      <Input
                        id="firstName"
                        value={firstName}
                        onChange={(e) => setFirstName(e.target.value)}
                        placeholder="Seu nome"
                      />
                      {errors.firstName && (
                        <p className="text-sm text-red-500">{errors.firstName}</p>
                      )}
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="lastName">Sobrenome *</Label>
                      <Input
                        id="lastName"
                        value={lastName}
                        onChange={(e) => setLastName(e.target.value)}
                        placeholder="Seu sobrenome"
                      />
                      {errors.lastName && (
                        <p className="text-sm text-red-500">{errors.lastName}</p>
                      )}
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label htmlFor="cpf">CPF *</Label>
                      <Input
                        id="cpf"
                        value={cpf}
                        onChange={(e) => setCpf(formatCPF(e.target.value))}
                        placeholder="000.000.000-00"
                        maxLength={14}
                      />
                      {errors.cpf && (
                        <p className="text-sm text-red-500">{errors.cpf}</p>
                      )}
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="birthDate">Data de Nascimento *</Label>
                      <Input
                        id="birthDate"
                        type="date"
                        value={birthDate}
                        onChange={(e) => setBirthDate(e.target.value)}
                      />
                      {errors.birthDate && (
                        <p className="text-sm text-red-500">{errors.birthDate}</p>
                      )}
                    </div>
                  </div>
                </>
              ) : (
                /* Formulário Pessoa Jurídica */
                <>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label htmlFor="cnpj">CNPJ *</Label>
                      <Input
                        id="cnpj"
                        value={cnpj}
                        onChange={(e) => setCnpj(formatCNPJ(e.target.value))}
                        placeholder="00.000.000/0000-00"
                        maxLength={18}
                      />
                      {errors.cnpj && (
                        <p className="text-sm text-red-500">{errors.cnpj}</p>
                      )}
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="companyName">Razão Social *</Label>
                      <Input
                        id="companyName"
                        value={companyName}
                        onChange={(e) => setCompanyName(e.target.value)}
                        placeholder="Nome da empresa"
                      />
                      {errors.companyName && (
                        <p className="text-sm text-red-500">{errors.companyName}</p>
                      )}
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label htmlFor="tradeName">Nome Fantasia</Label>
                      <Input
                        id="tradeName"
                        value={tradeName}
                        onChange={(e) => setTradeName(e.target.value)}
                        placeholder="Nome comercial"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="stateRegistration">Inscrição Estadual</Label>
                      <Input
                        id="stateRegistration"
                        value={stateRegistration}
                        onChange={(e) => setStateRegistration(e.target.value)}
                        placeholder="Opcional"
                      />
                    </div>
                  </div>

                  <div className="border-t pt-4">
                    <h4 className="font-medium mb-3">Dados do Responsável</h4>
                    <div className="grid grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <Label htmlFor="firstName">Nome *</Label>
                        <Input
                          id="firstName"
                          value={firstName}
                          onChange={(e) => setFirstName(e.target.value)}
                          placeholder="Nome do responsável"
                        />
                        {errors.firstName && (
                          <p className="text-sm text-red-500">{errors.firstName}</p>
                        )}
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="lastName">Sobrenome *</Label>
                        <Input
                          id="lastName"
                          value={lastName}
                          onChange={(e) => setLastName(e.target.value)}
                          placeholder="Sobrenome do responsável"
                        />
                        {errors.lastName && (
                          <p className="text-sm text-red-500">{errors.lastName}</p>
                        )}
                      </div>
                    </div>
                  </div>
                </>
              )}

              {/* Telefone - Comum */}
              <div className="space-y-2">
                <Label htmlFor="phone">Telefone</Label>
                <Input
                  id="phone"
                  value={phone}
                  onChange={(e) => setPhone(formatPhone(e.target.value))}
                  placeholder="(00) 00000-0000"
                  maxLength={15}
                />
              </div>

              {/* Endereço */}
              <div className="border-t pt-4">
                <h4 className="font-medium mb-3">Endereço</h4>
                <div className="space-y-4">
                  <div className="grid grid-cols-3 gap-4">
                    <div className="space-y-2">
                      <Label htmlFor="addressZipCode">CEP</Label>
                      <Input
                        id="addressZipCode"
                        value={addressZipCode}
                        onChange={(e) => setAddressZipCode(formatCEP(e.target.value))}
                        placeholder="00000-000"
                        maxLength={9}
                      />
                    </div>
                    <div className="col-span-2 space-y-2">
                      <Label htmlFor="addressStreet">Rua/Logradouro</Label>
                      <Input
                        id="addressStreet"
                        value={addressStreet}
                        onChange={(e) => setAddressStreet(e.target.value)}
                        placeholder="Nome da rua"
                      />
                    </div>
                  </div>

                  <div className="grid grid-cols-4 gap-4">
                    <div className="space-y-2">
                      <Label htmlFor="addressNumber">Número</Label>
                      <Input
                        id="addressNumber"
                        value={addressNumber}
                        onChange={(e) => setAddressNumber(e.target.value)}
                        placeholder="Nº"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="addressComplement">Complemento</Label>
                      <Input
                        id="addressComplement"
                        value={addressComplement}
                        onChange={(e) => setAddressComplement(e.target.value)}
                        placeholder="Apto, Sala..."
                      />
                    </div>
                    <div className="col-span-2 space-y-2">
                      <Label htmlFor="addressNeighborhood">Bairro</Label>
                      <Input
                        id="addressNeighborhood"
                        value={addressNeighborhood}
                        onChange={(e) => setAddressNeighborhood(e.target.value)}
                        placeholder="Nome do bairro"
                      />
                    </div>
                  </div>

                  <div className="grid grid-cols-3 gap-4">
                    <div className="col-span-2 space-y-2">
                      <Label htmlFor="addressCity">Cidade</Label>
                      <Input
                        id="addressCity"
                        value={addressCity}
                        onChange={(e) => setAddressCity(e.target.value)}
                        placeholder="Nome da cidade"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="addressState">Estado</Label>
                      <Select value={addressState} onValueChange={setAddressState}>
                        <SelectTrigger>
                          <SelectValue placeholder="UF" />
                        </SelectTrigger>
                        <SelectContent>
                          {BRAZILIAN_STATES.map((state) => (
                            <SelectItem key={state.value} value={state.value}>
                              {state.value}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                  </div>
                </div>
              </div>

              <div className="flex justify-end pt-4">
                <Button onClick={handleSaveProfile} disabled={saving}>
                  {saving ? (
                    <>
                      <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                      Salvando...
                    </>
                  ) : (
                    <>
                      <Check className="w-4 h-4 mr-2" />
                      Salvar Perfil
                    </>
                  )}
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Tab: Segurança */}
        <TabsContent value="security">
          <Card>
            <CardHeader>
              <CardTitle>Alterar Senha</CardTitle>
              <CardDescription>
                Atualize sua senha de acesso à plataforma
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="currentPassword">Senha Atual</Label>
                <div className="relative">
                  <Input
                    id="currentPassword"
                    type={showCurrentPassword ? 'text' : 'password'}
                    value={currentPassword}
                    onChange={(e) => setCurrentPassword(e.target.value)}
                    placeholder="Digite sua senha atual"
                  />
                  <button
                    type="button"
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-700"
                    onClick={() => setShowCurrentPassword(!showCurrentPassword)}
                  >
                    {showCurrentPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
                {errors.currentPassword && (
                  <p className="text-sm text-red-500">{errors.currentPassword}</p>
                )}
              </div>

              <div className="space-y-2">
                <Label htmlFor="newPassword">Nova Senha</Label>
                <div className="relative">
                  <Input
                    id="newPassword"
                    type={showNewPassword ? 'text' : 'password'}
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                    placeholder="Digite a nova senha (mínimo 6 caracteres)"
                  />
                  <button
                    type="button"
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-700"
                    onClick={() => setShowNewPassword(!showNewPassword)}
                  >
                    {showNewPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
                {errors.newPassword && (
                  <p className="text-sm text-red-500">{errors.newPassword}</p>
                )}
              </div>

              <div className="space-y-2">
                <Label htmlFor="confirmPassword">Confirmar Nova Senha</Label>
                <Input
                  id="confirmPassword"
                  type="password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  placeholder="Confirme a nova senha"
                />
                {errors.confirmPassword && (
                  <p className="text-sm text-red-500">{errors.confirmPassword}</p>
                )}
              </div>

              <div className="flex justify-end pt-4">
                <Button onClick={handleChangePassword} disabled={changingPassword}>
                  {changingPassword ? (
                    <>
                      <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                      Alterando...
                    </>
                  ) : (
                    <>
                      <Lock className="w-4 h-4 mr-2" />
                      Alterar Senha
                    </>
                  )}
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Tab: Pagamento */}
        <TabsContent value="payment">
          <Card>
            <CardHeader>
              <CardTitle>Método de Pagamento</CardTitle>
              <CardDescription>
                Gerencie seu cartão de crédito para cobrança
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Cartão Atual */}
              {paymentMethod?.has_payment_method && (
                <div className="p-4 border rounded-lg bg-slate-50">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <CreditCard className="w-8 h-8 text-slate-600" />
                      <div>
                        <p className="font-medium">
                          {getCardBrandIcon(paymentMethod.card_brand || 'unknown')}
                        </p>
                        <p className="text-sm text-slate-600">
                          •••• •••• •••• {paymentMethod.card_last_four}
                        </p>
                        <p className="text-xs text-slate-500">
                          Expira em {paymentMethod.exp_month?.toString().padStart(2, '0')}/{paymentMethod.exp_year}
                        </p>
                      </div>
                    </div>
                    <Button variant="destructive" size="sm" onClick={handleRemoveCard}>
                      Remover
                    </Button>
                  </div>
                </div>
              )}

              {/* Formulário de Novo Cartão */}
              <div className="space-y-4">
                <h4 className="font-medium">
                  {paymentMethod?.has_payment_method ? 'Trocar Cartão' : 'Adicionar Cartão'}
                </h4>
                
                <div className="space-y-2">
                  <Label htmlFor="cardNumber">Número do Cartão</Label>
                  <div className="relative">
                    <Input
                      id="cardNumber"
                      value={cardNumber}
                      onChange={(e) => setCardNumber(formatCardNumber(e.target.value))}
                      placeholder="0000 0000 0000 0000"
                      maxLength={19}
                    />
                    {cardNumber && (
                      <span className="absolute right-3 top-1/2 -translate-y-1/2 text-sm text-slate-500">
                        {detectCardBrand(cardNumber) !== 'unknown' && 
                          detectCardBrand(cardNumber).charAt(0).toUpperCase() + detectCardBrand(cardNumber).slice(1)}
                      </span>
                    )}
                  </div>
                  {errors.cardNumber && (
                    <p className="text-sm text-red-500">{errors.cardNumber}</p>
                  )}
                </div>

                <div className="space-y-2">
                  <Label htmlFor="cardHolder">Nome no Cartão</Label>
                  <Input
                    id="cardHolder"
                    value={cardHolder}
                    onChange={(e) => setCardHolder(e.target.value.toUpperCase())}
                    placeholder="NOME COMO ESTÁ NO CARTÃO"
                  />
                  {errors.cardHolder && (
                    <p className="text-sm text-red-500">{errors.cardHolder}</p>
                  )}
                </div>

                <div className="grid grid-cols-3 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="cardExpMonth">Mês</Label>
                    <Select value={cardExpMonth} onValueChange={setCardExpMonth}>
                      <SelectTrigger>
                        <SelectValue placeholder="MM" />
                      </SelectTrigger>
                      <SelectContent>
                        {Array.from({ length: 12 }, (_, i) => i + 1).map((month) => (
                          <SelectItem key={month} value={month.toString()}>
                            {month.toString().padStart(2, '0')}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    {errors.cardExpMonth && (
                      <p className="text-sm text-red-500">{errors.cardExpMonth}</p>
                    )}
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="cardExpYear">Ano</Label>
                    <Select value={cardExpYear} onValueChange={setCardExpYear}>
                      <SelectTrigger>
                        <SelectValue placeholder="AAAA" />
                      </SelectTrigger>
                      <SelectContent>
                        {Array.from({ length: 10 }, (_, i) => new Date().getFullYear() + i).map((year) => (
                          <SelectItem key={year} value={year.toString()}>
                            {year}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    {errors.cardExpYear && (
                      <p className="text-sm text-red-500">{errors.cardExpYear}</p>
                    )}
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="cardCvv">CVV</Label>
                    <Input
                      id="cardCvv"
                      value={cardCvv}
                      onChange={(e) => setCardCvv(e.target.value.replace(/\D/g, ''))}
                      placeholder="000"
                      maxLength={4}
                      type="password"
                    />
                    {errors.cardCvv && (
                      <p className="text-sm text-red-500">{errors.cardCvv}</p>
                    )}
                  </div>
                </div>

                <div className="flex justify-end pt-4">
                  <Button onClick={handleSaveCard} disabled={savingCard}>
                    {savingCard ? (
                      <>
                        <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                        Salvando...
                      </>
                    ) : (
                      <>
                        <CreditCard className="w-4 h-4 mr-2" />
                        {paymentMethod?.has_payment_method ? 'Atualizar Cartão' : 'Adicionar Cartão'}
                      </>
                    )}
                  </Button>
                </div>

                <p className="text-xs text-slate-500 text-center">
                  🔒 Seus dados de pagamento são processados de forma segura. 
                  Não armazenamos o número completo do cartão.
                </p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
