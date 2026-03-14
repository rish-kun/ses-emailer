import { Html, Head, Body, Container, Heading, Text, Hr, Button, Link } from '@react-email/components';

export default function Newsletter() {
    return (
        <Html>
            <Head />
            <Body style={{ backgroundColor: '#ffffff', fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif' }}>
                <Container style={{ margin: '0 auto', padding: '20px 0 48px', maxWidth: '580px' }}>
                    <Heading style={{ fontSize: '28px', letterSpacing: '-1px', lineHeight: '1.3', color: '#1a1a1a', fontWeight: '700', margin: '0 0 30px', textAlign: 'center' }}>
                        Monthly Newsletter
                    </Heading>
                    
                    <Text style={{ fontSize: '16px', lineHeight: '1.6', color: '#374151', margin: '0 0 24px' }}>
                        Hello there!
                    </Text>
                    
                    <Text style={{ fontSize: '16px', lineHeight: '1.6', color: '#374151', margin: '0 0 24px' }}>
                        Here's what's new this month:
                    </Text>
                    
                    <Heading as="h2" style={{ fontSize: '20px', lineHeight: '1.4', color: '#1a1a1a', fontWeight: '600', margin: '0 0 12px' }}>
                        🚀 New Features
                    </Heading>
                    <Text style={{ fontSize: '16px', lineHeight: '1.6', color: '#374151', margin: '0 0 24px' }}>
                        We've added several new features to improve your experience.
                    </Text>
                    
                    <Heading as="h2" style={{ fontSize: '20px', lineHeight: '1.4', color: '#1a1a1a', fontWeight: '600', margin: '0 0 12px' }}>
                        📊 Updates
                    </Heading>
                    <Text style={{ fontSize: '16px', lineHeight: '1.6', color: '#374151', margin: '0 0 30px' }}>
                        Performance improvements and bug fixes across the platform.
                    </Text>
                    
                    <Hr style={{ border: 'none', borderTop: '1px solid #e5e7eb', margin: '30px 0' }} />
                    
                    <Text style={{ fontSize: '14px', color: '#6b7280', margin: '0 0 16px' }}>
                        You're receiving this email because you subscribed to our newsletter.
                    </Text>
                    
                    <Text style={{ fontSize: '14px', color: '#9ca3af', margin: '0' }}>
                        © 2024 SES Emailer. All rights reserved.
                    </Text>
                </Container>
            </Body>
        </Html>
    );
}