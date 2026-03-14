'use client';

import { Button } from '@/components/ui/button';
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';

interface LGPDStepProps {
  onConsent: () => void;
  onDecline: () => void;
}

export function LGPDStep({ onConsent, onDecline }: LGPDStepProps) {
  return (
    <Card className="max-w-2xl mx-auto">
      <CardHeader>
        <CardTitle className="text-xl">Termo de Consentimento para Tratamento de Dados</CardTitle>
        <p className="text-sm text-muted-foreground">Pesquisa de Clima Organizacional – LGPD</p>
      </CardHeader>
      <CardContent>
        <div className="prose prose-sm max-w-none text-sm text-muted-foreground space-y-4 max-h-80 overflow-y-auto border rounded-lg p-4 bg-gray-50">
          <p>
            Este documento visa registrar a manifestação livre, informada e inequívoca pela qual o Titular concorda com
            o tratamento de seus dados pessoais para uma finalidade específica, em estrita conformidade com a Lei Geral
            de Proteção de Dados Pessoais (Lei nº 13.709/2018 - LGPD).
          </p>

          <h4 className="font-semibold text-foreground">1. Objetivo da Coleta</h4>
          <p>
            A presente pesquisa, realizada por meio da plataforma Vivamente360, tem como objetivo avaliar o clima
            organizacional e mapear fatores psicossociais no ambiente de trabalho, com base nas diretrizes da Norma
            Regulamentadora NR-1 do Ministério do Trabalho e Emprego.
          </p>

          <h4 className="font-semibold text-foreground">2. Dados Coletados</h4>
          <p>
            Serão coletados dados de natureza demográfica (gênero, faixa etária, tempo de empresa) e respostas ao
            questionário de avaliação psicossocial. Não serão coletados dados que permitam sua identificação direta,
            preservando seu anonimato.
          </p>

          <h4 className="font-semibold text-foreground">3. Base Legal</h4>
          <p>
            O tratamento dos dados tem como base legal o legítimo interesse do empregador (Art. 7º, IX, LGPD) e o
            cumprimento de obrigação legal (Art. 7º, II, LGPD), notadamente o dever de gestão dos riscos psicossociais
            previsto na NR-1.
          </p>

          <h4 className="font-semibold text-foreground">4. Finalidade e Uso dos Dados</h4>
          <p>
            Os dados serão utilizados exclusivamente para elaboração de relatórios estatísticos agregados sobre o clima
            organizacional. Em nenhuma hipótese os resultados individuais serão divulgados ou utilizados para fins
            de avaliação de desempenho individual.
          </p>

          <h4 className="font-semibold text-foreground">5. Armazenamento e Segurança</h4>
          <p>
            Os dados serão armazenados em servidores seguros, com criptografia em trânsito e em repouso. O período
            de retenção dos dados não excederá 5 (cinco) anos, salvo obrigação legal em contrário.
          </p>

          <h4 className="font-semibold text-foreground">6. Direitos do Titular</h4>
          <p>
            Nos termos dos Arts. 17 a 22 da LGPD, você tem direito a: confirmação e acesso aos seus dados; correção
            de dados incompletos ou incorretos; anonimização, bloqueio ou eliminação de dados desnecessários;
            portabilidade dos dados; e revogação do consentimento a qualquer momento.
          </p>

          <h4 className="font-semibold text-foreground">7. Voluntariedade</h4>
          <p>
            A participação nesta pesquisa é voluntária. Caso opte por não participar, nenhuma penalidade ou
            prejuízo será imposto. Sua decisão não afetará sua relação de emprego de nenhuma forma.
          </p>

          <h4 className="font-semibold text-foreground">8. Contato</h4>
          <p>
            Para exercer seus direitos ou obter mais informações sobre o tratamento de seus dados, entre em contato
            com o encarregado de dados (DPO) da sua empresa ou acesse as configurações de privacidade na plataforma
            Vivamente360.
          </p>
        </div>
      </CardContent>
      <CardFooter className="flex flex-col gap-3 pt-2">
        <Button className="w-full" size="lg" onClick={onConsent}>
          Li e concordo – Iniciar pesquisa
        </Button>
        <Button variant="outline" className="w-full" onClick={onDecline}>
          Não concordo – A pesquisa não será iniciada
        </Button>
      </CardFooter>
    </Card>
  );
}
