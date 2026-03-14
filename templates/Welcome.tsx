import { Html, Head, Body, Container, Heading, Text, Hr, Link } from '@react-email/components';

export default function Welcome() {
    return (
        <Html>
            <Head />
            <Body style={{ backgroundColor: '#f6f9fc', fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif' }}>
                <Container style={{ margin: '0 auto', padding: '20px 0 48px', maxWidth: '580px' }}>
                    <Heading style={{ fontSize: '24px', letterSpacing: '-0.5px', lineHeight: '1.3', color: '#484848', fontWeight: '700', margin: '0 0 20px' }}>
                        Welcome to SES Emailer!
                    </Heading>
                    <Text style={{ fontSize: '16px', lineHeight: '1.6', color: '#484848', margin: '0 0 20px' }}>
                        Thank you for joining us. We're excited to have you on board.
                    </Text>
                    <Text style={{ fontSize: '16px', lineHeight: '1.6', color: '#484848', margin: '0 0 20px' }}>
                        With SES Emailer, you can send beautiful emails to your audience with ease.
                    </Text>
                    <Hr style={{ border: 'none', borderTop: '1px solid #e0e0e0', margin: '20px 0' }} />
                    <Text style={{ fontSize: '14px', color: '#888888', margin: '0' }}>
                        Best regards,<br />The SES Emailer Team
                    </Text>
                </Container>
            </Body>
        </Html>
    );
}