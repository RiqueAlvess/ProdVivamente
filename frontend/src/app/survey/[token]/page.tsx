'use client';

import { useState, useEffect } from 'react';
import { useParams } from 'next/navigation';
import { Brain, CheckCircle, XCircle } from 'lucide-react';
import { LGPDStep } from '@/components/survey/lgpd-step';
import { DemographicsStep } from '@/components/survey/demographics-step';
import { QuestionStep } from '@/components/survey/question-step';
import { FeedbackStep } from '@/components/survey/feedback-step';
import { Card, CardContent } from '@/components/ui/card';
import api from '@/lib/api';
import type { SurveyData, Demographics, Answer } from '@/types';

type SurveyStep = 'loading' | 'lgpd' | 'demographics' | 'questions' | 'feedback' | 'success' | 'declined' | 'already_completed' | 'error';

export default function SurveyPage() {
  const { token } = useParams<{ token: string }>();
  const [step, setStep] = useState<SurveyStep>('loading');
  const [surveyData, setSurveyData] = useState<SurveyData | null>(null);
  const [demographics, setDemographics] = useState<Demographics | undefined>();
  const [answers, setAnswers] = useState<Record<number, number>>({});
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    async function fetchSurvey() {
      try {
        const { data } = await api.get<SurveyData>(`/survey/${token}/`);
        setSurveyData(data);
        if (data.already_completed) {
          setStep('already_completed');
        } else {
          setStep('lgpd');
        }
      } catch {
        setStep('error');
      }
    }
    fetchSurvey();
  }, [token]);

  function handleLGPDConsent() {
    setStep('demographics');
  }

  function handleLGPDDecline() {
    setStep('declined');
  }

  function handleDemographics(demo: Demographics) {
    setDemographics(demo);
    setStep('questions');
  }

  function handleDemographicsSkip() {
    setStep('questions');
  }

  function handleAnswerSelect(value: number) {
    const question = surveyData!.questions[currentQuestionIndex];
    setAnswers((prev) => ({ ...prev, [question.id]: value }));
  }

  function handleNextQuestion() {
    if (currentQuestionIndex < surveyData!.questions.length - 1) {
      setCurrentQuestionIndex((i) => i + 1);
    } else {
      setStep('feedback');
    }
  }

  function handlePreviousQuestion() {
    if (currentQuestionIndex > 0) {
      setCurrentQuestionIndex((i) => i - 1);
    }
  }

  async function handleSubmit(feedback?: string) {
    setIsSubmitting(true);
    try {
      const formattedAnswers: Answer[] = Object.entries(answers).map(([questionId, value]) => ({
        question_id: Number(questionId),
        value: value as 0 | 1 | 2 | 3 | 4,
      }));

      await api.post(`/survey/${token}/submit/`, {
        token,
        lgpd_consent: true,
        demographics,
        answers: formattedAnswers,
        feedback,
      });
      setStep('success');
    } catch {
      alert('Erro ao enviar respostas. Tente novamente.');
    } finally {
      setIsSubmitting(false);
    }
  }

  function handleFeedbackSkip() {
    handleSubmit(undefined);
  }

  const currentQuestion = surveyData?.questions?.[currentQuestionIndex];
  const selectedValue = currentQuestion ? answers[currentQuestion.id] : undefined;

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 py-8 px-4">
      {/* Header */}
      <div className="flex justify-center mb-8">
        <div className="flex items-center gap-2">
          <Brain className="h-8 w-8 text-blue-600" />
          <div>
            <p className="font-bold text-xl leading-none text-slate-800">VIVAMENTE</p>
            <p className="text-xs text-slate-500">360º – Pesquisa de Clima</p>
          </div>
        </div>
      </div>

      {surveyData && (step === 'lgpd' || step === 'demographics' || step === 'questions' || step === 'feedback') && (
        <div className="text-center mb-6">
          <p className="text-sm text-muted-foreground">{surveyData.company_name}</p>
          <p className="font-medium">{surveyData.campaign_name}</p>
        </div>
      )}

      {/* Steps */}
      <div className="max-w-2xl mx-auto">
        {step === 'loading' && (
          <div className="flex items-center justify-center h-40">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
          </div>
        )}

        {step === 'lgpd' && (
          <LGPDStep onConsent={handleLGPDConsent} onDecline={handleLGPDDecline} />
        )}

        {step === 'demographics' && (
          <DemographicsStep onNext={handleDemographics} onSkip={handleDemographicsSkip} />
        )}

        {step === 'questions' && currentQuestion && (
          <QuestionStep
            question={currentQuestion}
            currentIndex={currentQuestionIndex}
            totalQuestions={surveyData!.questions.length}
            selectedValue={selectedValue}
            onSelect={handleAnswerSelect}
            onNext={handleNextQuestion}
            onPrevious={handlePreviousQuestion}
          />
        )}

        {step === 'feedback' && (
          <FeedbackStep
            onSubmit={handleSubmit}
            onSkip={handleFeedbackSkip}
            isSubmitting={isSubmitting}
          />
        )}

        {step === 'success' && (
          <Card className="max-w-md mx-auto">
            <CardContent className="py-12 text-center">
              <CheckCircle className="h-16 w-16 text-green-500 mx-auto mb-4" />
              <h2 className="text-2xl font-bold mb-2">Obrigado!</h2>
              <p className="text-muted-foreground mb-4">
                Suas respostas foram registradas com sucesso. Sua participação é muito importante para melhorarmos
                o ambiente de trabalho.
              </p>
              <p className="text-sm text-muted-foreground">
                Você já pode fechar esta janela.
              </p>
            </CardContent>
          </Card>
        )}

        {step === 'declined' && (
          <Card className="max-w-md mx-auto">
            <CardContent className="py-12 text-center">
              <XCircle className="h-16 w-16 text-muted-foreground mx-auto mb-4" />
              <h2 className="text-xl font-semibold mb-2">Participação não confirmada</h2>
              <p className="text-muted-foreground">
                Você optou por não participar da pesquisa. Nenhum dado foi coletado.
              </p>
              <p className="text-sm text-muted-foreground mt-4">
                Você pode fechar esta janela.
              </p>
            </CardContent>
          </Card>
        )}

        {step === 'already_completed' && (
          <Card className="max-w-md mx-auto">
            <CardContent className="py-12 text-center">
              <CheckCircle className="h-16 w-16 text-blue-500 mx-auto mb-4" />
              <h2 className="text-xl font-semibold mb-2">Pesquisa já respondida</h2>
              <p className="text-muted-foreground">
                Você já respondeu a esta pesquisa. Obrigado pela sua participação!
              </p>
            </CardContent>
          </Card>
        )}

        {step === 'error' && (
          <Card className="max-w-md mx-auto">
            <CardContent className="py-12 text-center">
              <XCircle className="h-16 w-16 text-destructive mx-auto mb-4" />
              <h2 className="text-xl font-semibold mb-2">Link inválido</h2>
              <p className="text-muted-foreground">
                Este link de pesquisa é inválido ou expirou. Entre em contato com o RH da sua empresa.
              </p>
            </CardContent>
          </Card>
        )}
      </div>

      <p className="text-center text-xs text-muted-foreground mt-12">
        Plataforma VIVAMENTE 360º · Todos os dados são protegidos conforme a LGPD
      </p>
    </div>
  );
}
