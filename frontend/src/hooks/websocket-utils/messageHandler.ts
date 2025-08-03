import { useCallback } from "react";
import { type AppDispatch } from "@/store";
import {
    updateLastMessageTimestamp,
    setConnectionEstablished,
    startAssessment,
    setAssessmentRecovered,
    setAssessmentStarted,
    addChatMessage,
    setCurrentQuestion,
    setAnswerFeedback,
    updateProgress,
    completeAssessment,
    setError,
    addErrorLog,
    setInteractionType,
    updateChatHistory,
    type ChatMessage
} from "@/store/slices/assessmentSlice";

export interface WebSocketMessage {
    type: string;
    data?: any;
    error?: string;
    timestamp?: string;
}
export interface MessageHandlerContext {
    dispatch: AppDispatch;
    testId: number
    sendMessage: (message: any) => void
    generateChatMessage: (
        type: ChatMessage['type'],
        content: string,
        options?: any
    ) => ChatMessage
    assessmentState: any,
}
type MessageHandler = (message: WebSocketMessage) => void
export const getMessageHandler = (context: MessageHandlerContext) => {
    const { dispatch, testId, sendMessage, generateChatMessage, assessmentState } = context;

    const messageHandlers: Record<string, MessageHandler> = {
        auth_success: (message: WebSocketMessage) => {
            if (message?.data.recovered_assessment) {
                dispatch(addChatMessage(generateChatMessage('system', 'It appears you already have started the assessment, Recovering your assessment, Make sure to have stable internet connection result in multiple voilation will automatically submit the test')))
            }
            dispatch(setConnectionEstablished({
                connection_id: message.data.connection_id,
                user_id: message.data.user_id,
                test_id: testId,
            }));
        },
        assessment_started: (message: WebSocketMessage) => {
            dispatch(setAssessmentStarted({
                assessment_id: message.data.assessment_id,
                thread_id: message.data.thread_id,
                test_id: message.data.test_id,
                test_name: message.data.test_name,
            }));
            const welcomeMessage = generateChatMessage(
                'system',
                'Assessment started! Your first question will appear shortly.'
            );
            dispatch(addChatMessage(welcomeMessage));
        },
        assessment_recovered: (message: WebSocketMessage) => {
            dispatch(setAssessmentRecovered({
                assessment_id: message.data.assessment_id,
                thread_id: message.data.thread_id,
                progress: message.data.progress.answered_questions / message.data.progress.total_questions * 100
            }));
            sendMessage({ type: 'get_question' });
        },
        question: (message: WebSocketMessage) => {
            const raw_question = message.data.question;
            const options = raw_question?.options?.map((option: any) => ({ "option_id": option[0], "option": option.slice(2) }))
            console.log(options)

            // Store in Redux state for compatibility
            dispatch(setCurrentQuestion({
                question_id: message.data.question_id,
                thread_id: message.data.thread_id,
                question: {
                    text: raw_question.prompt,
                    options: options,
                    difficulty: raw_question.meta.difficulty,
                    skill: raw_question.skill,
                    time_limit: message.data.question.time_limit
                }
            }));

            const questionChatMessage = generateChatMessage(
                'ai_question',
                raw_question.prompt,
                options,
            );
            questionChatMessage.question_id = message.data.question_id;

            dispatch(addChatMessage(questionChatMessage));
            dispatch(setInteractionType('waiting_response'));
        },
        answer_feedback: (message: WebSocketMessage) => {
            dispatch(setAnswerFeedback({
                question_id: message.data.question_id,
                feedback: {
                    correct: message.data.feedback.correct,
                    selected_option: message.data.feedback.selected_option,
                    correct_answer: message.data.feedback.correct_answer,
                    message: message.data.feedback.message
                },
                progress: message.data.percentage_complete,
                thread_id: message.data.thread_id
            }));
            // Show processing message
            dispatch(setInteractionType('processing'));
            sendMessage({ type: 'get_question' });

        },
        progress_update: (message: WebSocketMessage) => {
            dispatch(updateProgress(message?.data.percentage_complete));

        },
        assessment_completed: (message: WebSocketMessage) => {
            dispatch(completeAssessment());
        },
        error: (message: WebSocketMessage) => {
            const errorData = message.data || {};
            dispatch(setError({
                message: errorData.error || 'Unknown error occurred',
                code: errorData.code,
                details: errorData.details,
                recoverable: errorData.recoverable
            }));

            // Handle specific error types based on error message content
            const errorMessage = errorData.error || '';

            if (errorMessage.includes('Authentication failed') || errorMessage.includes('Invalid token')) {
                dispatch(addErrorLog({
                    type: 'auth_error',
                    message: 'Authentication failed - token invalid or expired',
                    recoverable: false
                }));
            } else if (errorMessage.includes('Access denied')) {
                dispatch(addErrorLog({
                    type: 'access_error',
                    message: 'Access denied - no permission for this test',
                    recoverable: false
                }));
            } else if (errorMessage.includes('Test not found')) {
                dispatch(addErrorLog({
                    type: 'test_error',
                    message: 'Test not found',
                    recoverable: false
                }));
            } else if (errorMessage.includes('Failed to generate question')) {
                dispatch(addErrorLog({
                    type: 'question_error',
                    message: 'Question generation failed',
                    recoverable: true
                }));
                // setTimeout(() => {
                //     sendMessage({ type: 'get_question' });
                // }, 2000);
            }
        },
        system_message: (message: WebSocketMessage) => {
            dispatch(addErrorLog({
                type: 'system_message',
                message: message.data.message,
                recoverable: true
            }));
        },
        pong: (message: WebSocketMessage) => {
            dispatch(updateLastMessageTimestamp());
        },
        test_info: (message: WebSocketMessage) => {
            console.log('Test Info Response:', message.data);

        },
    }

    return useCallback((message: WebSocketMessage) => {
        dispatch(updateLastMessageTimestamp())
        console.log(message)
        const handler = messageHandlers[message.type];

        if (!handler) {
            dispatch(addErrorLog({
                type: 'unknown_message',
                message: `Received unknown message type: ${message.type}`,
                recoverable: true
            }));
            return;
        }


        try {
            handler(message)
        } catch (error) {
            console.error(`Error handling message type '${message.type}':`, error);
            dispatch(addErrorLog({
                type: 'handler_error',
                message: `Failed to handle message type: ${message.type}`,
                recoverable: true
            }));
        }
    }, [messageHandlers, dispatch])
}