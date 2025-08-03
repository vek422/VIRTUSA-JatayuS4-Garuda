import { useEffect, useRef, useCallback, useState } from 'react';
import { useAppDispatch, useAppSelector } from '../store';
import {
    setConnectionStatus,
    startAssessment,
    submitAnswer as submitAnswerAction,
    setError,
    addErrorLog,
    updateLastMessageTimestamp,
    incrementReconnectAttempts,
    resetReconnectAttempts,
    resetAssessment,
    addChatMessage,
    setInteractionType,
    clearChatHistory,
    type ChatMessage
} from '../store/slices/assessmentSlice';
import { getMessageHandler } from './websocket-utils/messageHandler';
import { type WebSocketMessage } from './websocket-utils/messageHandler';
import { WS_URL } from '@/config';
console.log(WS_URL)
interface UseAssessmentWebSocketOptions {
    testId: number;
    autoStart?: boolean;
    maxReconnectAttempts?: number;
    reconnectDelay?: number;
    websocketUrl?: string;
}

export const useAssessmentWebSocket = ({
    testId,
    autoStart = true,
    maxReconnectAttempts = 5,
    reconnectDelay = 1000,
    websocketUrl = WS_URL
}: UseAssessmentWebSocketOptions) => {
    const dispatch = useAppDispatch();
    const { token } = useAppSelector(state => state.auth); const assessmentState = useAppSelector(state => state.assessment);
    const [processMessage, setProcessMessage] = useState("");
    const websocketRef = useRef<WebSocket | null>(null);
    const reconnectTimeoutRef = useRef<number | null>(null);
    const reconnectDelayRef = useRef(reconnectDelay);
    const isManualDisconnectRef = useRef(false);
    const processMessageTimeoutRef = useRef<number | null>(null);// WebSocket URL construction
    const getWebSocketUrl = useCallback(() => {
        if (!token) {
            throw new Error('No authentication token available');
        }
        return `${websocketUrl}/ws/assessment?test_id=${testId}&token=${encodeURIComponent(token)}`;
    }, [websocketUrl, testId, token]);


    // Helper function to generate chat messages
    const generateChatMessage = useCallback((
        type: ChatMessage['type'],
        content: string,
        options?: any,
        metadata?: any
    ): ChatMessage => {
        return {
            id: `msg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
            type,
            content,
            timestamp: new Date().toISOString(),
            options,
            metadata
        };
    }, []); const updateProcesMessage = (message: string) => {
        // Clear any existing timeout
        if (processMessageTimeoutRef.current) {
            clearTimeout(processMessageTimeoutRef.current);
            processMessageTimeoutRef.current = null;
        }

        let displayMessage = "";
        switch (message) {
            case "get_question":
                displayMessage = "Fetching Next Question";
                break;
            case "complete_assessment":
                displayMessage = "Submitting Assessment";
                break;
            case "submit_answer":
                displayMessage = "Submitting the response";
                break;
            case "start_assessment":
                displayMessage = "Preparing your assessment";
                break;
        }

        if (displayMessage) {
            setProcessMessage(displayMessage);

            // Set a timeout to clear the message after minimum duration (1.5 seconds)
            processMessageTimeoutRef.current = window.setTimeout(() => {
                setProcessMessage("");
                processMessageTimeoutRef.current = null;
            }, 2000);
        }
    }

    // Function to clear process message immediately (used when new question arrives)
    const clearProcessMessage = useCallback(() => {
        if (processMessageTimeoutRef.current) {
            clearTimeout(processMessageTimeoutRef.current);
            processMessageTimeoutRef.current = null;
        }
        setProcessMessage("");
    }, []);
    // Send message through WebSocket
    const sendMessage = useCallback((message: any) => {
        if (websocketRef.current?.readyState === WebSocket.OPEN) {
            const messageWithTimestamp = {
                ...message,
                timestamp: new Date().toISOString()
            };

            // Debug logging
            if (import.meta.env.DEV) {
                console.log('📤 Sending:', messageWithTimestamp);
            }

            updateProcesMessage(message.type);
            websocketRef.current.send(JSON.stringify(messageWithTimestamp));
            dispatch(updateLastMessageTimestamp());
        } else {
            dispatch(addErrorLog({
                type: 'send_error',
                message: 'Cannot send message - WebSocket not connected',
                recoverable: true
            }));
        }
    }, [dispatch]);
    const sendDebugMessage = () => {
        sendMessage({ type: "get_test_info" })
    }
    const messageHandler = getMessageHandler({ assessmentState, dispatch, generateChatMessage, sendMessage, testId });
    // Connect to WebSocket
    const connect = useCallback(() => {
        try {
            dispatch(setConnectionStatus('connecting'));
            const wsUrl = getWebSocketUrl();
            const ws = new WebSocket(wsUrl);

            ws.onopen = () => {
                console.log('WebSocket connected to assessment');
                websocketRef.current = ws;
                dispatch(resetReconnectAttempts());
                reconnectDelayRef.current = reconnectDelay;
                isManualDisconnectRef.current = false;
            };

            ws.onmessage = (event) => {
                try {
                    const message: WebSocketMessage = JSON.parse(event.data);

                    // Debug logging
                    if (import.meta.env.DEV) {
                        console.log('📨 Received:', message);
                    }
                    if (message.type == "question")
                        clearProcessMessage();
                    messageHandler(message);
                } catch (error) {
                    console.error('Error parsing WebSocket message:', error);
                    dispatch(addErrorLog({
                        type: 'parse_error',
                        message: 'Failed to parse WebSocket message',
                        details: error instanceof Error ? error.message : 'Unknown parse error',
                        recoverable: true
                    }));
                }
            };

            ws.onclose = (event) => {
                console.log('WebSocket disconnected:', event.code, event.reason);
                websocketRef.current = null;
                dispatch(setConnectionStatus('disconnected'));

                // Only attempt reconnection if it wasn't a manual disconnect
                if (!isManualDisconnectRef.current &&
                    !event.wasClean &&
                    assessmentState.reconnect_attempts < maxReconnectAttempts) {
                    scheduleReconnect();
                }
            };

            ws.onerror = (error) => {
                console.error('WebSocket error:', error);
                dispatch(setError({
                    message: 'WebSocket connection error',
                    recoverable: true
                }));
            };

        } catch (error) {
            dispatch(setError({
                message: error instanceof Error ? error.message : 'Failed to connect to WebSocket',
                recoverable: true
            }));
        }
    }, [dispatch, getWebSocketUrl, assessmentState.reconnect_attempts, maxReconnectAttempts, reconnectDelay]);

    // Schedule reconnection with exponential backoff
    const scheduleReconnect = useCallback(() => {
        dispatch(incrementReconnectAttempts());
        dispatch(setConnectionStatus('reconnecting'));

        reconnectTimeoutRef.current = setTimeout(() => {
            connect();
        }, reconnectDelayRef.current) as unknown as number;

        // Exponential backoff with max delay of 30 seconds
        reconnectDelayRef.current = Math.min(reconnectDelayRef.current * 2, 30000);
    }, [dispatch, connect, assessmentState.reconnect_attempts]);

    // Disconnect WebSocket
    const disconnect = useCallback(() => {
        isManualDisconnectRef.current = true;

        if (reconnectTimeoutRef.current) {
            clearTimeout(reconnectTimeoutRef.current);
            reconnectTimeoutRef.current = null;
        }

        if (websocketRef.current) {
            websocketRef.current.close(1000, 'Manual disconnect');
            websocketRef.current = null;
        }

        dispatch(setConnectionStatus('disconnected'));
    }, [dispatch]);
    const submitAnswer = useCallback((questionId: string, selectedOption: string) => {

        const optionText = assessmentState.current_question?.options.find(
            opt => opt.option_id === selectedOption
        )?.option || selectedOption;

        dispatch(submitAnswerAction({
            question_id: questionId,
            selected_option: selectedOption,
            option_text: optionText
        }));
        const userResponseMessage = generateChatMessage(
            'user_response',
            `${selectedOption}. ${optionText}`
        );
        dispatch(addChatMessage(userResponseMessage));

        setProcessMessage("Evaluating your response");
        dispatch(setInteractionType('processing'));

        sendMessage({
            type: 'submit_answer',
            data: {
                question_id: questionId,
                selected_option: selectedOption
            }
        });
    }, [sendMessage, dispatch, assessmentState.current_question, generateChatMessage]);

    const requestQuestion = useCallback(() => {
        sendMessage({ type: 'get_question' });
    }, [sendMessage]);

    const requestProgress = useCallback(() => {
        sendMessage({ type: 'get_progress' });
    }, [sendMessage]);

    const completeAssessmentRequest = useCallback(() => {
        sendMessage({ type: 'complete_assessment' });
    }, [sendMessage]);

    const startAssessmentSession = useCallback(() => {
        dispatch(startAssessment({ test_id: testId }));
        sendMessage({
            type: 'start_assessment',
            data: { test_id: testId }
        });
    }, [dispatch, sendMessage, testId]); const resetAssessmentSession = useCallback(() => {
        dispatch(resetAssessment());
        dispatch(clearChatHistory());
        disconnect();
    }, [dispatch, disconnect]);


    const sendChatMessage = useCallback((message: string) => {
        sendMessage({
            type: 'chat_message',
            data: { message }
        });
    }, [sendMessage]);

    const sendHeartbeat = useCallback(() => {
        sendMessage({ type: 'heartbeat' });
    }, [sendMessage]);

    useEffect(() => {
        let heartbeatInterval: number | null = null;

        if (assessmentState.connection_status === 'connected') {
            heartbeatInterval = setInterval(() => {
                sendHeartbeat();
            }, 30000) as unknown as number; // Send heartbeat every 30 seconds
        }

        return () => {
            if (heartbeatInterval) {
                clearInterval(heartbeatInterval);
            }
        };
    }, [assessmentState.connection_status, sendHeartbeat]);

    // Initialize connection on mount
    useEffect(() => {
        if (token && testId) {
            connect();
        }        // Cleanup on unmount
        return () => {
            if (reconnectTimeoutRef.current) {
                clearTimeout(reconnectTimeoutRef.current);
            }
            if (processMessageTimeoutRef.current) {
                clearTimeout(processMessageTimeoutRef.current);
            }
            if (websocketRef.current) {
                websocketRef.current.close();
            }
        };
    }, [connect, token, testId]);    // Return hook interface
    return {
        // State
        connectionStatus: assessmentState.connection_status,
        assessmentStarted: assessmentState.assessment_started,
        assessmentCompleted: assessmentState.assessment_completed,
        currentQuestion: assessmentState.current_question,
        progress: assessmentState.progress,
        currentError: assessmentState.current_error,
        reconnectAttempts: assessmentState.reconnect_attempts,
        test_name: assessmentState.test_name,
        processMessage,
        setProcessMessage,
        // Chat state
        chatHistory: assessmentState.chat_history,
        interactionType: assessmentState.current_interaction_type,

        // Actions
        connect,
        disconnect,
        submitAnswer,
        requestQuestion,
        requestProgress,
        completeAssessment: completeAssessmentRequest,
        startAssessment: startAssessmentSession,
        resetAssessment: resetAssessmentSession,
        sendChatMessage,
        sendHeartbeat,
        sendMessage, // Add generic sendMessage function
        sendDebugMessage,
        // Utils
        isConnected: assessmentState.connection_status === 'connected',
        isConnecting: assessmentState.connection_status === 'connecting',
        isReconnecting: assessmentState.connection_status === 'reconnecting',
        hasError: !!assessmentState.current_error
    };
};
